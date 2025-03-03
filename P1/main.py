import re
import os
import sys

# ==========================
# Conversión de BibTeX a RIS
# ==========================

# Expresiones regulares para extraer campos de BibTeX (incluyendo month y day)
patterns = {
    "author": re.compile(r'author\s*=\s*{(.*?)}', re.DOTALL),
    "title": re.compile(r'title\s*=\s*{(.*?)}', re.DOTALL),
    "year": re.compile(r'year\s*=\s*{(\d{4})}'),
    "month": re.compile(r'month\s*=\s*{(.*?)}', re.DOTALL),
    "day": re.compile(r'day\s*=\s*{(.*?)}', re.DOTALL),
    "volume": re.compile(r'volume\s*=\s*{(\d+)}'),
    "number": re.compile(r'number\s*=\s*{(\d+)}'),
    "pages": re.compile(r'pages\s*=\s*{(\d+)\s*[-–]{1,2}\s*(\d+)}'),
    "doi": re.compile(r'doi\s*=\s*{(.*?)}'),
    "url": re.compile(r'url\s*=\s*{(.*?)}'),
    "publisher": re.compile(r'publisher\s*=\s*{(.*?)}', re.DOTALL),
    "journal": re.compile(r'journal\s*=\s*{(.*?)}', re.DOTALL),
    "booktitle": re.compile(r'booktitle\s*=\s*{(.*?)}', re.DOTALL),
    "editor": re.compile(r'editor\s*=\s*{(.*?)}', re.DOTALL),
    "edition": re.compile(r'edition\s*=\s*{(.*?)}'),
    "keywords": re.compile(r'keywords\s*=\s*{(.*?)}'),
    "issn": re.compile(r'issn\s*=\s*{(.*?)}'),
    "isbn": re.compile(r'isbn\s*=\s*{(.*?)}'),
    "address": re.compile(r'address\s*=\s*{(.*?)}', re.DOTALL),
    "abstract": re.compile(r'abstract\s*=\s*{(.*?)}', re.DOTALL),
}

# Mapeo de campos BibTeX a etiquetas RIS
bibtex_to_ris = {
    "author": "AU",
    "title": "TI",
    "year": "PY",
    "volume": "VL",
    "number": "IS",
    "pages": ("SP", "EP"),
    "doi": "DO",  # El DOI se asigna a DO
    "url": "UR",
    "publisher": "PB",
    "journal": "JO",
    "booktitle": "BT",
    "editor": "ED",
    "edition": "ET",
    "keywords": "KW",
    "issn": "SN",
    "isbn": "SN",
    "address": "CY",
    "abstract": "AB",
}

# Función para limpiar caracteres especiales (se eliminan llaves y se realizan algunos reemplazos simples)
def clean_text(text):
    # Reemplazos simples para acentuaciones (puedes ampliar según necesidad)
    text = re.sub(r'{\\[a-z]\{([a-zA-Z])\}}', r'\1', text)
    text = re.sub(r'{\\([a-zA-Z])}', r'\1', text)
    text = re.sub(r'[{}]', '', text)
    return text.strip()

# Función para dividir autores o editores (se asume separación por " and ")
def split_authors(authors_str):
    authors = re.split(r'\s+and\s+', authors_str.strip())
    return [clean_text(author.strip()) for author in authors]

# Función para convertir una entrada BibTeX a formato RIS
def convert_bibtex_to_ris(bibtex_entry):
    ris_entries = []
    
    # Determinar el tipo de entrada
    if re.search(r'@article\s*{', bibtex_entry, re.IGNORECASE):
        ris_entries.append("TY  - JOUR")
    elif re.search(r'@inproceedings\s*{', bibtex_entry, re.IGNORECASE):
        ris_entries.append("TY  - CONF")
    elif re.search(r'@book\s*{', bibtex_entry, re.IGNORECASE):
        ris_entries.append("TY  - BOOK")
    else:
        ris_entries.append("TY  - GEN")
    
    # Extraer el ID (clave de la entrada)
    id_match = re.search(r'@\w+\s*{([^,]+)', bibtex_entry)
    
    # Procesar autores
    author_match = patterns["author"].search(bibtex_entry)
    if author_match:
        authors = split_authors(author_match.group(1))
        for author in authors:
            ris_entries.append(f"AU  - {author}")
    
    # Procesar editores
    editor_match = patterns["editor"].search(bibtex_entry)
    if editor_match:
        editors = split_authors(editor_match.group(1))
        for editor in editors:
            ris_entries.append(f"ED  - {editor}")
    
    # Añadir año (PY) y fecha completa (DA) con month y day si están presentes
    year_match = patterns["year"].search(bibtex_entry)
    if year_match:
        year = year_match.group(1)
        ris_entries.append(f"PY  - {year}")
        month_match = patterns["month"].search(bibtex_entry)
        day_match = patterns["day"].search(bibtex_entry)
        if month_match and day_match:
            month_text = month_match.group(1).strip()
            month_map = {
                "jan": "01", "feb": "02", "mar": "03", "apr": "04",
                "may": "05", "jun": "06", "jul": "07", "aug": "08",
                "sep": "09", "oct": "10", "nov": "11", "dec": "12"
            }
            month_num = month_map.get(month_text.lower(), month_text)
            day = day_match.group(1).strip()
            ris_entries.append(f"DA  - {year}/{month_num}/{day}")
        else:
            ris_entries.append(f"DA  - {year}//")
    
    # Procesar título
    title_match = patterns["title"].search(bibtex_entry)
    if title_match:
        ris_entries.append(f"{bibtex_to_ris['title']}  - {clean_text(title_match.group(1))}")
    
    # Según el tipo, procesar journal o booktitle
    if re.search(r'@article\s*{', bibtex_entry, re.IGNORECASE):
        journal_match = patterns["journal"].search(bibtex_entry)
        if journal_match:
            ris_entries.append(f"{bibtex_to_ris['journal']}  - {clean_text(journal_match.group(1))}")
    elif re.search(r'@inproceedings\s*{', bibtex_entry, re.IGNORECASE):
        booktitle_match = patterns["booktitle"].search(bibtex_entry)
        if booktitle_match:
            ris_entries.append(f"{bibtex_to_ris['booktitle']}  - {clean_text(booktitle_match.group(1))}")
    
    # Procesar abstract
    abstract_match = patterns["abstract"].search(bibtex_entry)
    if abstract_match:
        abstract = clean_text(abstract_match.group(1))
        ris_entries.append(f"{bibtex_to_ris['abstract']}  - {abstract}")
    
    # Procesar ISBN/ISSN
    isbn_match = patterns["isbn"].search(bibtex_entry)
    if isbn_match:
        ris_entries.append(f"{bibtex_to_ris['isbn']}  - {clean_text(isbn_match.group(1))}")
    else:
        issn_match = patterns["issn"].search(bibtex_entry)
        if issn_match:
            ris_entries.append(f"{bibtex_to_ris['issn']}  - {clean_text(issn_match.group(1))}")
    
    # Procesar páginas
    pages_match = patterns["pages"].search(bibtex_entry)
    if pages_match:
        start_page = pages_match.group(1)
        end_page = pages_match.group(2)
        ris_entries.append(f"{bibtex_to_ris['pages'][0]}  - {start_page}")
        ris_entries.append(f"{bibtex_to_ris['pages'][1]}  - {end_page}")
    
    # Procesar otros campos: publisher, address, volume y number
    for field in ["publisher", "address", "volume", "number"]:
        match = patterns[field].search(bibtex_entry)
        if match:
            ris_entries.append(f"{bibtex_to_ris[field]}  - {clean_text(match.group(1))}")
    
    # Procesar URL
    url_match = patterns["url"].search(bibtex_entry)
    if url_match:
        ris_entries.append(f"{bibtex_to_ris['url']}  - {clean_text(url_match.group(1))}")
    
    # Procesar DOI
    doi_match = patterns["doi"].search(bibtex_entry)
    if doi_match:
        ris_entries.append(f"{bibtex_to_ris['doi']}  - {clean_text(doi_match.group(1))}")
    
    # Agregar la clave de la entrada (ID)
    if id_match:
        ris_entries.append(f"ID  - {id_match.group(1).strip()}")
    
    # Línea final del registro
    ris_entries.append("ER  -")
    
    return "\n".join(ris_entries)

def process_bibtex_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Separa las entradas individuales; si no se encuentra separación, se procesa todo el contenido
        bibtex_entries = re.findall(r'(@\w+\{[^@]*?\n\})', content, re.DOTALL)
        if not bibtex_entries:
            bibtex_entries = [content]
        
        ris_content = ""
        for entry in bibtex_entries:
            ris_content += convert_bibtex_to_ris(entry) + "\n\n"
        
        return ris_content.strip()
    except Exception as e:
        return f"Error al procesar el archivo: {str(e)}"

# ==========================
# Conversión de RIS a BibTeX
# ==========================

# Función para convertir una única entrada RIS a formato BibTeX
def convert_ris_to_bibtex(ris_entry):
    # Separar líneas y almacenar los campos encontrados.
    # Para etiquetas que pueden aparecer varias veces (por ejemplo, AU, ED, KW) se usan listas.
    fields = {}
    multiline_tags = ["AU", "ED", "KW"]
    pages = {}  # Para SP y EP
    bib_type = None
    citation_id = None
    da_value = None

    for line in ris_entry.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^([A-Z]{2})\s*-\s*(.*)$', line)
        if m:
            tag = m.group(1)
            value = m.group(2).strip()
            if tag == "TY":
                # Determinar el tipo de entrada según el valor
                type_value = value.strip()
                if type_value == "JOUR":
                    bib_type = "Article"
                elif type_value == "CONF":
                    bib_type = "InProceedings"
                elif type_value == "BOOK":
                    bib_type = "Book"
                else:
                    bib_type = "Misc"
            elif tag == "ID":
                citation_id = value
            elif tag == "DA":
                da_value = value
            elif tag == "SP":
                pages["start"] = value
            elif tag == "EP":
                pages["end"] = value
            else:
                if tag in multiline_tags:
                    fields.setdefault(tag, []).append(value)
                else:
                    fields[tag] = value

    # Si no se encontró tipo, se asigna Misc
    if not bib_type:
        bib_type = "Misc"
    # Si no se encontró clave, se genera una clave por defecto
    if not citation_id:
        citation_id = "Clave"

    # Iniciar la construcción de la entrada BibTeX
    bibtex_lines = []
    bibtex_lines.append(f"@{bib_type}{{{citation_id},")
    # Campos de autores
    if "AU" in fields:
        authors = " and ".join(fields["AU"])
        bibtex_lines.append(f"  author = {{{authors}}},")
    # Campos de editores
    if "ED" in fields:
        editors = " and ".join(fields["ED"])
        bibtex_lines.append(f"  editor = {{{editors}}},")
    # Título
    if "TI" in fields:
        bibtex_lines.append(f"  title = {{{fields['TI']}}},")
    # Según el tipo, asignar journal o booktitle
    if bib_type == "Article" and "JO" in fields:
        bibtex_lines.append(f"  journal = {{{fields['JO']}}},")
    if bib_type == "InProceedings" and "BT" in fields:
        bibtex_lines.append(f"  booktitle = {{{fields['BT']}}},")
    # Año
    if "PY" in fields:
        bibtex_lines.append(f"  year = {{{fields['PY']}}},")
    # Si DA existe, extraer month y day
    if da_value:
        parts = da_value.split("/")
        if len(parts) == 3:
            # Convertir mes numérico a abreviatura
            month_map = {
                "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
                "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
                "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
            }
            month_abbr = month_map.get(parts[1], parts[1])
            bibtex_lines.append(f"  month = {{{month_abbr}}},")
            bibtex_lines.append(f"  day = {{{parts[2]}}},")
    # Volume
    if "VL" in fields:
        bibtex_lines.append(f"  volume = {{{fields['VL']}}},")
    # Número (issue)
    if "IS" in fields:
        bibtex_lines.append(f"  number = {{{fields['IS']}}},")
    # Páginas
    if "start" in pages and "end" in pages:
        bibtex_lines.append(f"  pages = {{{pages['start']}--{pages['end']}}},")
    # DOI
    if "DO" in fields:
        bibtex_lines.append(f"  doi = {{{fields['DO']}}},")
    # URL
    if "UR" in fields:
        bibtex_lines.append(f"  url = {{{fields['UR']}}},")
    # Publisher
    if "PB" in fields:
        bibtex_lines.append(f"  publisher = {{{fields['PB']}}},")
    # Address
    if "CY" in fields:
        bibtex_lines.append(f"  address = {{{fields['CY']}}},")
    # Abstract
    if "AB" in fields:
        bibtex_lines.append(f"  abstract = {{{fields['AB']}}},")
    # ISBN/ISSN (se asigna al campo isbn)
    if "SN" in fields:
        bibtex_lines.append(f"  isbn = {{{fields['SN']}}},")
    # Edition
    if "ET" in fields:
        bibtex_lines.append(f"  edition = {{{fields['ET']}}},")
    # Keywords
    if "KW" in fields:
        keywords = " and ".join(fields["KW"]) if isinstance(fields["KW"], list) else fields["KW"]
        bibtex_lines.append(f"  keywords = {{{keywords}}},")
    
    # Eliminar la coma del último campo
    if bibtex_lines[-1].endswith(","):
        bibtex_lines[-1] = bibtex_lines[-1][:-1]
    
    bibtex_lines.append("}")
    return "\n".join(bibtex_lines)

def process_ris_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Se asume que cada entrada RIS está separada por líneas en blanco
        ris_entries = re.split(r'\n\s*\n', content.strip())
        if not ris_entries:
            ris_entries = [content]
        
        bibtex_entries = []
        for entry in ris_entries:
            entry = entry.strip()
            if entry:
                bibtex_entries.append(convert_ris_to_bibtex(entry))
        return "\n\n".join(bibtex_entries)
    except Exception as e:
        return f"Error al procesar el archivo RIS: {str(e)}"

# ==========================
# Función principal: Detecta la extensión y convierte
# ==========================

def main():
    try:
        input_file = input("Ingrese el nombre del archivo a convertir (.bib o .ris): ").strip()
        if not os.path.isfile(input_file):
            print(f"Error: El archivo '{input_file}' no existe.")
            return
        
        base, ext = os.path.splitext(input_file)
        ext = ext.lower()
        if ext == ".bib":
            output_file = base + "_generado.ris"
            print(f"Procesando archivo BibTeX '{input_file}'...")
            result = process_bibtex_file(input_file)
        elif ext == ".ris":
            output_file = base + "_generado.bib"
            print(f"Procesando archivo RIS '{input_file}'...")
            result = process_ris_file(input_file)
        else:
            print("Error: La extensión del archivo debe ser .bib o .ris")
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Conversión completada. Resultado guardado en '{output_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
