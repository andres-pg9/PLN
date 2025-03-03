import re
import os
import sys

# Expresiones regulares mejoradas, incluyendo month y day
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
    "doi": "DO",  # Actualizado: el DOI se asigna a DO
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

# Función para limpiar caracteres especiales en nombres
def clean_text(text):
    # Elimina escapes tipo {\v{R}}epa → Řepa
    text = re.sub(r'{\\[a-z]\{([a-zA-Z])\}}', r'\1', text)
    # Elimina escapes tipo {\'a} → á
    text = re.sub(r'{\\([a-zA-Z])}', r'\1', text)
    # Elimina llaves restantes
    text = re.sub(r'[{}]', '', text)
    return text.strip()

# Función para dividir autores o editores correctamente
def split_authors(authors_str):
    authors = re.split(r'\s+and\s+', authors_str.strip())  # Divide por 'and'
    return [clean_text(author.strip()) for author in authors]

# Función para convertir BibTeX a RIS
def convert_bibtex_to_ris(bibtex_entry):
    ris_entries = []
    
    # Determinar el tipo de entrada (@article, @inproceedings, @book, etc.)
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
            # Conversión de abreviatura del mes a número
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
    
    # Según el tipo de entrada, procesar journal o booktitle
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
    
    # Agregar la clave de la entrada (ID) al final
    if id_match:
        ris_entries.append(f"ID  - {id_match.group(1).strip()}")
    
    # Línea final del registro
    ris_entries.append("ER  -")
    
    return "\n".join(ris_entries)

# Procesar múltiples entradas BibTeX en un archivo
def process_bibtex_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividir el archivo en entradas individuales de BibTeX
        bibtex_entries = re.findall(r'(@\w+\{[^@]*?\n\})', content, re.DOTALL)
        if not bibtex_entries:
            bibtex_entries = [content]
        
        ris_content = ""
        for entry in bibtex_entries:
            ris_content += convert_bibtex_to_ris(entry) + "\n\n"
        
        return ris_content.strip()
    except Exception as e:
        return f"Error al procesar el archivo: {str(e)}"

def main():
    try:
        input_file = input("Ingrese el nombre del archivo BibTeX (.bib) a convertir: ")
        if not os.path.isfile(input_file):
            print(f"Error: El archivo '{input_file}' no existe.")
            return
        
        output_file = os.path.splitext(input_file)[0] + "_generado.ris"
        print(f"Procesando archivo '{input_file}'...")
        ris_content = process_bibtex_file(input_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ris_content)
        
        print(f"Conversión completada. Resultado guardado en '{output_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
