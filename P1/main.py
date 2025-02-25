import re
import pandas as pd

def load_equivalences(csv_path):
    """Carga las equivalencias de etiquetas desde el archivo CSV."""
    df = pd.read_csv(csv_path)
    return dict(zip(df['BibTeX Field'], df['RIS Tag']))

def bibtex_to_ris(bibtex_text, equivalences):
    """Convierte un texto en formato BibTeX a RIS."""
    ris_lines = ["TY  - JOUR"]  # Tipo de referencia fija para artículos
    
    for key, ris_tag in equivalences.items():
        pattern = rf"{key}\s*=\s*\{{(.*?)\}}"
        match = re.search(pattern, bibtex_text, re.DOTALL)
        if match:
            value = match.group(1)
            
            # Manejar autores separados por 'and'
            if key == "author":
                authors = value.split(" and ")
                for author in authors:
                    ris_lines.append(f"AU  - {author.strip()}")
            elif key == "pages":
                pages = value.split("-")
                ris_lines.append(f"SP  - {pages[0].strip()}")
                ris_lines.append(f"EP  - {pages[1].strip()}")
            else:
                ris_lines.append(f"{ris_tag}  - {value.strip()}")
    
    # Extraer ID
    match = re.match(r"@\w+\{(.*?),", bibtex_text)
    if match:
        ris_lines.append(f"ID  - {match.group(1).strip()}")
    
    ris_lines.append("ER  -")  # Fin del registro
    return "\n".join(ris_lines)

def ris_to_bibtex(ris_text, equivalences):
    """Convierte un texto en formato RIS a BibTeX."""
    bibtex_lines = ["@article{"]
    fields = {}
    
    for line in ris_text.split("\n"):
        match = re.match(r"(\w{2})  - (.*)", line)
        if match:
            ris_tag, value = match.groups()
            if ris_tag in equivalences.values():
                bib_key = [key for key, tag in equivalences.items() if tag == ris_tag][0]
                if bib_key == "author":
                    fields.setdefault("author", []).append(value)
                elif bib_key in ["pages"]:
                    fields["pages"] = fields.get("pages", "") + ("-" if "pages" in fields else "") + value
                else:
                    fields[bib_key] = value
            elif ris_tag == "ID":
                bibtex_lines[0] += f"{value},"
    
    for key, value in fields.items():
        if isinstance(value, list):
            value = " and ".join(value)
        bibtex_lines.append(f"    {key} = {{{value}}},")
    
    bibtex_lines.append("}")
    return "\n".join(bibtex_lines)

# Cargar equivalencias
equivalences = load_equivalences("tag_equivalence.csv")

# Ejemplo de uso
bibtex_example = """@article{Smith2023,
author = {Smith, John and Doe, Jane},
title = {Título del artículo sobre un tema interesante},
journal = {Revista de Ciencia Avanzada},
year = {2023},
volume = {15},
number = {2},
pages = {125-148},
} """

ris_output = bibtex_to_ris(bibtex_example, equivalences)
print("\n--- RIS OUTPUT ---\n", ris_output)

ris_example = """TY  - JOUR
AU  - Smith, John
AU  - Doe, Jane
TI  - Título del artículo sobre un tema interesante
JO  - Revista de Ciencia Avanzada
PY  - 2023
VL  - 15
IS  - 2
SP  - 125
EP  - 148
ID  - Smith2023
ER  -"""

bibtex_output = ris_to_bibtex(ris_example, equivalences)
print("\n--- BIBTEX OUTPUT ---\n", bibtex_output)
