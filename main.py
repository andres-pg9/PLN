import re
import os

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

bibtex_to_ris = {
    "author": "AU",
    "title": "TI",
    "year": "PY",
    "volume": "VL",
    "number": "IS",
    "pages": ("SP", "EP"),
    "doi": "DO",
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

def clean_text(text):
    # Reemplazos simples para acentuaciones y eliminación de llaves
    text = re.sub(r'{\\[a-z]\{([a-zA-Z])\}}', r'\1', text)
    text = re.sub(r'{\\([a-zA-Z])}', r'\1', text)
    return re.sub(r'[{}]', '', text).strip()

def get_clean_field(key, entry):
    # Extrae y limpia el campo 'key' de una entrada.
    m = patterns.get(key).search(entry)
    return clean_text(m.group(1)) if m else None

def split_authors(authors_str):
    return [clean_text(a.strip()) for a in re.split(r'\s+and\s+', authors_str.strip())]

def split_keywords(keywords_str):
    # Separa por comas y elimina espacios sobrantes
    return [clean_text(k) for k in re.split(r',\s*', keywords_str.strip()) if k.strip()]

def add_field(ris_lines, bib_key, ris_tag, entry, multi=False):
    value = get_clean_field(bib_key, entry)
    if value:
        if multi:
            # Para keywords, se usa split_keywords; para autores/editores, split_authors
            if bib_key == "keywords":
                values = split_keywords(value)
            else:
                values = split_authors(value)
            for v in values:
                ris_lines.append(f"{ris_tag}  - {v}")
        else:
            ris_lines.append(f"{ris_tag}  - {value}")

def convert_bibtex_to_ris(bibtex_entry):
    ris_lines = []
    # Determinar el tipo de entrada
    if re.search(r'@article\s*{', bibtex_entry, re.IGNORECASE):
        ris_lines.append("TY  - JOUR")
    elif re.search(r'@inproceedings\s*{', bibtex_entry, re.IGNORECASE):
        ris_lines.append("TY  - CONF")
    else:
        ris_lines.append("TY  - GEN")
    
    id_match = re.search(r'@\w+\s*{([^,]+)', bibtex_entry)
    
    add_field(ris_lines, "author", bibtex_to_ris["author"], bibtex_entry, multi=True)
    add_field(ris_lines, "editor", bibtex_to_ris["editor"], bibtex_entry, multi=True)
    
    # Año (PY) solamente; se descarta DA ya que no está definido en las equivalencias.
    year = get_clean_field("year", bibtex_entry)
    if year:
        ris_lines.append(f"{bibtex_to_ris['year']}  - {year}")
    
    add_field(ris_lines, "title", bibtex_to_ris["title"], bibtex_entry)
    
    # Según tipo, journal o booktitle
    if re.search(r'@article\s*{', bibtex_entry, re.IGNORECASE):
        add_field(ris_lines, "journal", bibtex_to_ris["journal"], bibtex_entry)
    elif re.search(r'@inproceedings\s*{', bibtex_entry, re.IGNORECASE):
        add_field(ris_lines, "booktitle", bibtex_to_ris["booktitle"], bibtex_entry)
    
    add_field(ris_lines, "abstract", bibtex_to_ris["abstract"], bibtex_entry)
    
    # ISBN/ISSN
    isbn = get_clean_field("isbn", bibtex_entry)
    if isbn:
        ris_lines.append(f"{bibtex_to_ris['isbn']}  - {isbn}")
    else:
        issn = get_clean_field("issn", bibtex_entry)
        if issn:
            ris_lines.append(f"{bibtex_to_ris['issn']}  - {issn}")
    
    # Páginas
    m_pages = patterns["pages"].search(bibtex_entry)
    if m_pages:
        ris_lines.append(f"{bibtex_to_ris['pages'][0]}  - {m_pages.group(1)}")
        ris_lines.append(f"{bibtex_to_ris['pages'][1]}  - {m_pages.group(2)}")
    
    # Otros campos
    for field in ["publisher", "address", "volume", "number"]:
        add_field(ris_lines, field, bibtex_to_ris[field], bibtex_entry)
    
    add_field(ris_lines, "url", bibtex_to_ris["url"], bibtex_entry)
    add_field(ris_lines, "doi", bibtex_to_ris["doi"], bibtex_entry)
    
    add_field(ris_lines, "keywords", bibtex_to_ris["keywords"], bibtex_entry, multi=True)
    
    if id_match:
        ris_lines.append(f"ID  - {id_match.group(1).strip()}")
    ris_lines.append("ER  -")
    return "\n".join(ris_lines)

def process_bibtex_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        bib_entries = re.findall(r'(@\w+\{[^@]*?\n\})', content, re.DOTALL) or [content]
        return "\n\n".join(convert_bibtex_to_ris(entry) for entry in bib_entries)
    except Exception as e:
        return f"Error al procesar el archivo: {str(e)}"

def convert_ris_to_bibtex(ris_entry):
    fields = {}
    multiline_tags = ["AU", "ED", "KW"]
    pages = {}
    bib_type = None
    citation_id = None
    da_value = None

    for line in ris_entry.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^([A-Z]{2})\s*-\s*(.*)$', line)
        if m:
            tag, value = m.group(1), m.group(2).strip()
            if tag == "TY":
                bib_type = {"JOUR": "Article", "CONF": "InProceedings", "BOOK": "Book"}.get(value, "Misc")
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

    if not bib_type:
        bib_type = "Misc"
    if not citation_id:
        citation_id = "Clave"
    
    bibtex_lines = [f"@{bib_type}{{{citation_id},"]
    if "AU" in fields:
        bibtex_lines.append(f"  author = {{{' and '.join(fields['AU'])}}},")
    if "ED" in fields:
        bibtex_lines.append(f"  editor = {{{' and '.join(fields['ED'])}}},")
    if "TI" in fields:
        bibtex_lines.append(f"  title = {{{fields['TI']}}},")
    if bib_type == "Article" and "JO" in fields:
        bibtex_lines.append(f"  journal = {{{fields['JO']}}},")
    if bib_type == "InProceedings" and "BT" in fields:
        bibtex_lines.append(f"  booktitle = {{{fields['BT']}}},")
    if "PY" in fields:
        bibtex_lines.append(f"  year = {{{fields['PY']}}},")
    # Se omite DA pues no forma parte de las equivalencias
    if "VL" in fields:
        bibtex_lines.append(f"  volume = {{{fields['VL']}}},")
    if "IS" in fields:
        bibtex_lines.append(f"  number = {{{fields['IS']}}},")
    if "start" in pages and "end" in pages:
        bibtex_lines.append(f"  pages = {{{pages['start']}--{pages['end']}}},")
    if "DO" in fields:
        bibtex_lines.append(f"  doi = {{{fields['DO']}}},")
    if "UR" in fields:
        bibtex_lines.append(f"  url = {{{fields['UR']}}},")
    if "PB" in fields:
        bibtex_lines.append(f"  publisher = {{{fields['PB']}}},")
    if "CY" in fields:
        bibtex_lines.append(f"  address = {{{fields['CY']}}},")
    if "AB" in fields:
        bibtex_lines.append(f"  abstract = {{{fields['AB']}}},")
    if "SN" in fields:
        bibtex_lines.append(f"  isbn = {{{fields['SN']}}},")
    if "ET" in fields:
        bibtex_lines.append(f"  edition = {{{fields['ET']}}},")
    if "KW" in fields:
        kw = " and ".join(fields["KW"]) if isinstance(fields["KW"], list) else fields["KW"]
        bibtex_lines.append(f"  keywords = {{{kw}}},")
    
    if bibtex_lines[-1].endswith(","):
        bibtex_lines[-1] = bibtex_lines[-1][:-1]
    bibtex_lines.append("}")
    return "\n".join(bibtex_lines)

def process_ris_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ris_entries = re.split(r'\n\s*\n', content.strip()) or [content]
        return "\n\n".join(convert_ris_to_bibtex(entry.strip()) for entry in ris_entries if entry.strip())
    except Exception as e:
        return f"Error al procesar el archivo RIS: {str(e)}"

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
