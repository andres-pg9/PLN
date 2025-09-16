import csv
import re
import requests
import time
import spacy
# Cargar modelo spaCy una sola vez
nlp = spacy.load("en_core_web_sm")
from bs4 import BeautifulSoup   
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# =============== Funcion para obtener articulos de arXiv ==========================
def obtain_arxiv_csv(name="arxiv_raw_corpus.csv"):
    URLS = [
        "https://arxiv.org/list/cs.CL/recent?skip=0&show=2000",
        "https://arxiv.org/list/cs.CV/recent?skip=0&show=2000"
    ]
    articles_data = []
    arxiv_count = 0
    max_articles_per_url = 75  #  150 en total de las 2 secciones

    print("\n===== INICIANDO EXTRACCION DE ARXIV =====")

    for url in URLS:
        category = url.split('/')[4]
        print(f"Procesando categoría: {category}")
        
        r = requests.get(url=url)
        soup = BeautifulSoup(r.content, 'html5lib')

        cnt = 0
        dt = soup.find_all("dt")

        for d in dt:
            abst = d.find("a", title="Abstract")
            if not abst:
                continue

            ref = requests.get(url='https://arxiv.org/' + abst["href"])
            soup_ref = BeautifulSoup(ref.content, "html5lib")

            # DOI
            doi_html = soup_ref.find("a", id="arxiv-doi-link")
            doi = doi_html.text.strip().replace("https://doi.org/", "") if doi_html else "N/A"

            # Titulo
            title_html = soup_ref.find("h1", attrs={"class": "title"})
            match = re.search(r"^Title:(.*)", title_html.text, re.MULTILINE)
            title = match.group(1).strip() if match else "N/A"

            cnt += 1
            arxiv_count += 1
            print(f"Extraído artículo ArXiv {cnt}/{max_articles_per_url} de {category}: {title[:50]}...")

            # Secciones
            section_html = soup_ref.find("td", attrs={"class": "subjects"})
            sections = section_html.text.strip() if section_html else "N/A"
            sections_list = [s.strip() for s in sections.split(";")]
            sections_str = ", ".join(sections_list)

            # Fecha
            date_html = soup_ref.find("div", attrs={"class": "submission-history"})
            date = "N/A"
            if date_html:
                date_match = re.search(r"(\d{1,2} \w+ \d{4})", date_html.text)
                if date_match:
                    raw_date = date_match.group(1)
                    parsed_date = datetime.strptime(raw_date, "%d %b %Y")
                    date = parsed_date.strftime("%d/%m/%Y")

            # Autores
            authors_html = soup_ref.find("div", attrs={"class": "authors"})
            authors = re.sub(r"^Authors:\s*", "", authors_html.text)
            authors_str = ", ".join([author.strip() for author in authors.split(",")])

            # Abstract
            abstract_html = soup_ref.find("blockquote", attrs={"class": "abstract"})
            match = re.search(r"^Abstract:(.*)", abstract_html.text.strip(), re.MULTILINE)
            abstract = match.group(1).strip() if match else "N/A"

            # Agregar datos
            articles_data.append({
                "DOI": doi,
                "Title": title,
                "Authors": authors_str,
                "Abstract": abstract,
                "Section": sections_str,
                "Date": date
            })

            if cnt == max_articles_per_url:
                break
        print(f"ArXiv: {cnt} artículos extraídos de la categoría {category}.")

    # Guardar en CSV
    with open(name, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["DOI", "Title", "Authors", "Abstract", "Section", "Date"], delimiter="\t")
        writer.writeheader()
        writer.writerows(articles_data)

    print(f"Archivo {name} guardado con éxito.")
    return arxiv_count

#======================= Funcion para obtener articulos de PubMed =========================
def obtain_pubmed_csv(name="pubmed_raw_corpus.csv"):
    base_url = "https://pubmed.ncbi.nlm.nih.gov/trending/"
    headers = {"User-Agent": "Mozilla/5.0"}
    articles = []
    visited_articles = set()
    page = 1
    articles_needed = 150 # Numero de articulos
    pubmed_count = 0

    print("\n===== INICIANDO EXTRACCION DE PUBMED =====")

    while len(articles) < articles_needed:
        print(f"Procesando página {page} de PubMed...")
        trending_url = f"{base_url}?page={page}"
        response = requests.get(trending_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select("a.docsum-title")

            if not links:
                print(f"No hay más artículos en la página {page}.")
                break

            for link in links:
                article_id = link["href"].split("/")[-2]
                if article_id in visited_articles:
                    continue
                visited_articles.add(article_id)

                article_url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/?format=pubmed"

                try:
                    article_response = requests.get(article_url, headers=headers)
                    article_response.raise_for_status()

                    content = article_response.text
                    lines = content.split("\n")
                    data = {
                        "DOI": "No",
                        "Title": "",
                        "Authors": [],
                        "Abstract": "",
                        "Journal": "",
                        "Date": ""
                    }

                    collecting_abstract = False

                    for line in lines:
                        if line.startswith("TI  -"):
                            data["Title"] = line.replace("TI  -", "").strip()
                        elif line.startswith("AU  -"):
                            data["Authors"].append(line.replace("AU  -", "").strip())
                        elif line.startswith("AB  -"):
                            collecting_abstract = True
                            data["Abstract"] += line.replace("AB  -", "").strip() + " "
                        elif collecting_abstract:
                            if line.startswith(("FAU", "AD", "LA", "PT", "PL", "TA", "JT", "CI")):
                                collecting_abstract = False
                            else:
                                data["Abstract"] += line.strip() + " "
                        elif line.startswith("JT  -"):
                            data["Journal"] = line.replace("JT  -", "").strip()
                        elif line.startswith("DP  -"):
                            raw_date = line.replace("DP  -", "").strip()
                            try:
                                parsed_date = datetime.strptime(raw_date, "%Y %b %d")
                            except:
                                try:
                                    parsed_date = datetime.strptime(raw_date, "%Y %b")
                                except:
                                    try:
                                        parsed_date = datetime.strptime(raw_date, "%Y")
                                    except:
                                        parsed_date = None
                            data["Date"] = parsed_date.strftime("%d/%m/%Y") if parsed_date else "N/A"
                        elif line.startswith("AID -") and "[doi]" in line:
                            data["DOI"] = line.split(" [doi]")[0].replace("AID -", "").strip()

                    data["Authors"] = ", ".join(data["Authors"])
                    articles.append(data)
                    pubmed_count += 1

                    title_display = data["Title"][:50] + "..." if len(data["Title"]) > 50 else data["Title"]
                    print(f"Extraído artículo PubMed {pubmed_count}/{articles_needed}: {title_display}")

                    if len(articles) >= articles_needed:
                        break

                    time.sleep(1)

                except requests.exceptions.RequestException as e:
                    print(f"Error al obtener el artículo {article_id}: {e}")
                    continue
        else:
            print(f"Error al cargar la página {page}. Código {response.status_code}")
            break

        page += 1

    # Guardar CSV
    with open(name, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["DOI", "Title", "Authors", "Abstract", "Journal", "Date"], delimiter="\t")
        writer.writeheader()
        writer.writerows(articles)

    print(f"PubMed: {pubmed_count} artículos extraídos y guardados en {name}")
    return pubmed_count

#=================================== Normalizar Texto ===================================================
def normalize_text(text):
    doc = nlp(text)
    tokens = []
    for token in doc:
        if token.is_stop and token.pos_ in ["DET", "ADP", "CCONJ", "PRON"]:
            continue
        if token.is_punct or token.like_num or token.is_space:
            tokens.append(token.text)
        else:
            tokens.append(token.lemma_.lower())
    return " ".join(tokens)




def normalize_csv(input_csv, output_csv, title_col="Title", abstract_col="Abstract"):
    print(f"\nNormalizando archivo: {input_csv}")
    df = pd.read_csv(input_csv, delimiter="\t")
    df[title_col] = df[title_col].astype(str).apply(normalize_text)
    df[abstract_col] = df[abstract_col].astype(str).apply(normalize_text)
    df.to_csv(output_csv, sep="\t", index=False)
    print(f"Archivo normalizado guardado en: {output_csv}")

#=============================================================================================================

def generate_all_text_representations(input_csv, base_filename, title_col="Title", abstract_col="Abstract"):
    print(f"\nGenerando representaciones vectoriales desde: {input_csv}")
    df = pd.read_csv(input_csv, delimiter="\t")

    # Definir tipos de vectorizacion
    vectorizers = {
        "frecuencia": CountVectorizer,
        "binario": lambda **kwargs: CountVectorizer(binary=True, **kwargs),
        "tfidf": TfidfVectorizer
    }

    # Definir n-gramas, por unigramas y bigramas
    ngramas = {
        "unigramas": (1, 1),
        "bigramas": (2, 2)
    }

    # Definir campos (Title y Abstract)
    campos = {
        "title": df[title_col].fillna(""),
        "abstract": df[abstract_col].fillna("")
    }


    token_pattern = r"(?u)\w+|[^\w\s]"

    for campo_nombre, textos in campos.items():
        for ngrama_nombre, ngram_range in ngramas.items():
            for vector_nombre, vectorizador_func in vectorizers.items():
                print(f"- {campo_nombre.upper()} | {ngrama_nombre.upper()} | {vector_nombre.upper()}")

                vectorizador = vectorizador_func(ngram_range=ngram_range, token_pattern=token_pattern)
                matriz = vectorizador.fit_transform(textos)

                output_data = {
                    "vector": matriz,
                    "vectorizer": vectorizador
                }

                output_filename = f"{base_filename}_{campo_nombre}_{ngrama_nombre}_{vector_nombre}.pkl"

                with open(output_filename, "wb") as f:
                    pickle.dump(output_data, f)

                print(f"Guardado en {output_filename}")

# ========================== Leer archivo Ris o Bib ==================================
def read_query_file(filepath):
    ext = filepath.lower().split(".")[-1]
    title = ""
    abstract = ""

    if ext == "bib":
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().lower().startswith("title"):
                    title = line.split("=", 1)[1].strip().strip("{},").strip()
                elif line.strip().lower().startswith("abstract"):
                    abstract = line.split("=", 1)[1].strip().strip("{},").strip()

    elif ext == "ris":
     with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        collecting_abstract = False

        for line in lines:
            if line.startswith("TI  -"):
                title += line.replace("TI  -", "").strip() + " "
                collecting_abstract = False
            elif line.startswith("AB  -"):
                abstract += line.replace("AB  -", "").strip() + " "
                collecting_abstract = True
            elif collecting_abstract:
                if re.match(r"^[A-Z]{2}  -", line): 
                    collecting_abstract = False
                else:
                    abstract += line.strip() + " "

    else:
        print("Formato no soportado. Usa un archivo .bib o .ris")
        return "", ""

    # LOG DE VERIFICACION
    print("\nArchivo leído correctamente:")
    print(f"Titulo detectado: {title[:80]}{'...' if len(title) > 80 else ''}")
    print(f"Resumen detectado: {abstract[:80]}{'...' if len(abstract) > 80 else ''}")

    return title.strip(), abstract.strip()



def comparar_con_ambos_corpus(query_file):
    # Leer archivo .bib o .ris
    titulo, resumen = read_query_file(query_file)
    if not titulo and not resumen:
        print("No se encontró ni título ni resumen en el archivo.")
        return

    # Campo a comparar
    comparar_campo = input("¿Comparar 'title' o 'abstract'?: ").strip().lower()
    if comparar_campo not in ["title", "abstract"]:
        print("Opción inválida. Debe ser 'title' o 'abstract'.")
        return

    texto = titulo if comparar_campo == "title" else resumen
    if not texto:
        print(f"El campo '{comparar_campo}' no está presente en el archivo.")
        return

    # Seleccionar la configuracion 
    ngrama = input("¿Tipo de n-grama? (unigramas / bigramas): ").strip().lower()
    vector_tipo = input("¿Tipo de vector? (frecuencia / binario / tfidf): ").strip().lower()

    if ngrama not in ["unigramas", "bigramas"] or vector_tipo not in ["frecuencia", "binario", "tfidf"]:
        print("Configuración inválida.")
        return

    # Normalizar texto
    texto_normalizado = normalize_text(texto)

    for corpus in ["arxiv", "pubmed"]:
        print(f"\nComparando contra el corpus de {corpus.upper()}...")

        # Construir ruta al pkl
        pkl_path = f"{corpus}_{comparar_campo}_{ngrama}_{vector_tipo}.pkl"

        try:
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
        except FileNotFoundError:
            print(f"No se encontró el archivo {pkl_path}")
            continue

        matriz_corpus = data["vector"]
        vectorizer = data["vectorizer"]

        # Vectorizar texto nuevo
        vector_nuevo = vectorizer.transform([texto_normalizado])

        # Calcular similitud coseno
        similitudes = cosine_similarity(vector_nuevo, matriz_corpus)[0]
        top_10 = sorted(enumerate(similitudes), key=lambda x: x[1], reverse=True)[:10]

        print(f"Documentos similares ({comparar_campo}):")
        for idx, score in top_10:
            print(f"   - Documento #{idx} → Similitud: {round(score, 4)}")




# ==================    Menu interfaz  ================================
if __name__ == "__main__":
    print("===== MENÚ DE EXTRACCIÓN =====")
    print("1. Extraer artículos de arXiv")
    print("2. Extraer artículos de PubMed")
    print("3. Salir")
    print("4. Normalizar textos extraídos")
    print("5. Generar representaciones vectoriales")
    print("6 leer archivos")




    opcion = input("Seleccione una opción (1/2/3/4/5/6): ")

    if opcion == "1":
        obtain_arxiv_csv()
    elif opcion == "2":
        obtain_pubmed_csv()
    elif opcion == "3":
        print("Saliendo del programa...")
    elif opcion == "4":
        normalize_csv("arxiv_raw_corpus.csv", "arxiv_normalized_corpus.csv")
        normalize_csv("pubmed_raw_corpus.csv", "pubmed_normalized_corpus.csv")
    elif opcion == "5":
        generate_all_text_representations("arxiv_normalized_corpus.csv", "arxiv")
        generate_all_text_representations("pubmed_normalized_corpus.csv", "pubmed")
    elif opcion == "6":
        query_file = input("Nombre del archivo .bib o .ris: ").strip()
        comparar_con_ambos_corpus(query_file)        
    else:
        print("Opción no válida.")
