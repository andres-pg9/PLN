import re

# Expresiones regulares para cada campo
patterns = {
    "author": re.compile(r'author\s*=\s*{(.*?)}', re.DOTALL),
    "title": re.compile(r'title\s*=\s*{(.*?)}', re.DOTALL),
    "year": re.compile(r'year\s*=\s*{(\d{4}(/\d{2}/\d{2})?)}'),
    "volume": re.compile(r'volume\s*=\s*{(\d+)}'),
    "number": re.compile(r'number\s*=\s*{(\d+)}'),
    "pages": re.compile(r'pages\s*=\s*{(\d+)\s*--\s*(\d+)}'),
    "doi": re.compile(r'doi\s*=\s*{(.*?)}'),
    "url": re.compile(r'url\s*=\s*{(.*?)}'),
    "publisher": re.compile(r'publisher\s*=\s*{(.*?)}'),
    "journal": re.compile(r'journal\s*=\s*{(.*?)}'),
    "booktitle": re.compile(r'booktitle\s*=\s*{(.*?)}'),
    "editor": re.compile(r'editor\s*=\s*{(.*?)}', re.DOTALL),
    "edition": re.compile(r'edition\s*=\s*{(.*?)}'),
    "keywords": re.compile(r'keywords\s*=\s*{(.*?)}'),
    "issn": re.compile(r'issn\s*=\s*{(.*?)}'),
    "isbn": re.compile(r'isbn\s*=\s*{(.*?)}'),
    "address": re.compile(r'address\s*=\s*{(.*?)}'),
    "abstract": re.compile(r'abstract\s*=\s*{(.*?)}', re.DOTALL),
    "ID": re.compile(r'@(?:article|inproceedings)\s*{([^,]+)'),
    "@article": re.compile(r'@article\s*{'),
    "@inproceedings": re.compile(r'@inproceedings\s*{'),
}

# Mapeo de campos BibTeX a etiquetas RIS
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
    "booktitle": "BT",  # CORRECCIÓN: booktitle debe ser BT en lugar de T2
    "editor": "ED",
    "edition": "ET",
    "keywords": "KW",
    "issn": "SN",
    "isbn": "SN",
    "address": "CY",
    "abstract": "AB",
    "ID": "ID",
    "@article": "TY  - JOUR",
    "@inproceedings": "TY  - CONF",
}

# Función para limpiar caracteres especiales en nombres
def clean_text(text):
    text = re.sub(r'{\\([a-zA-Z])}', r'\1', text)  # Elimina escapes tipo {\'a} → á
    text = re.sub(r'[{}]', '', text)  # Elimina llaves restantes
    return text.strip()

# Función para dividir autores o editores correctamente
def split_authors(authors_str):
    authors = re.split(r'\s+and\s+', authors_str.strip())  # Divide por 'and'
    return [clean_text(author.strip()) for author in authors]

# Función para convertir BibTeX a RIS
def convert_bibtex_to_ris(bibtex_entry):
    ris_entries = []

    # Extraer el tipo de entrada (@article o @inproceedings)
    if patterns["@article"].search(bibtex_entry):
        ris_entries.append(bibtex_to_ris["@article"])
    elif patterns["@inproceedings"].search(bibtex_entry):
        ris_entries.append(bibtex_to_ris["@inproceedings"])

    # Extraer el ID
    match = patterns["ID"].search(bibtex_entry)
    if match:
        ris_entries.append(f"ID  - {match.group(1)}")

    # Extraer otros campos
    for field, pattern in patterns.items():
        if field not in ["ID", "@article", "@inproceedings"]:
            match = pattern.search(bibtex_entry)
            if match:
                ris_tag = bibtex_to_ris[field]

                if field in ["author", "editor"]:
                    names = split_authors(match.group(1))
                    for name in names:
                        ris_entries.append(f"{ris_tag}  - {name}")

                elif isinstance(ris_tag, tuple):  # Campos con múltiples valores (páginas)
                    ris_entries.append(f"{ris_tag[0]}  - {match.group(1)}")
                    ris_entries.append(f"{ris_tag[1]}  - {match.group(2)}")

                else:
                    ris_entries.append(f"{ris_tag}  - {clean_text(match.group(1))}")

    # Agregar fin de referencia (ER)
    ris_entries.append("ER  -")

    return "\n".join(ris_entries)

# Ejemplo de uso
bibtex_entry = """
@Article{Fatima2025,
author={Fatima, N. Sabiyath
and Deepika, G.
and Anthonisamy, Arun
and Chitra, R. Jothi
and Muralidharan, J.
and Alagarsamy, Manjunathan
and Ramyasree, Kummari},
title={Enhanced Facial Emotion Recognition Using Vision Transformer Models},
journal={Journal of Electrical Engineering {\&} Technology},
year={2025},
month={Jan},
day={29},
abstract={Automation of facial emotion recognition is an important branch of artificial intelligence and computer vision that has many potential applications in mental health diagnostics, human--computer interaction and security. The existing methods, however, usually have weaknesses in robustness, scalability and computational efficiency. This work proposes a self-attention-based Vision Transformer method that treats images as sequences of patches to capture global dependencies and spatial relations more effectively than other methods. The model is trained and evaluated using a large-scale dataset. On average, the model achieves an overall accuracy of 97{\%}, with good precision, recall and F1 scores in most emotion categories. The model performed better and was more robust to variations in illumination and facial pose compared to other existing methods. This work takes a step forward in facial emotion recognition technology, providing a large-scale and efficient solution for real-world applications. Facial Emotion Recognition, a New Vision Transformer Based on Self-Attention for Machine Learning.},
issn={2093-7423},
doi={10.1007/s42835-024-02118-w},
url={https://doi.org/10.1007/s42835-024-02118-w}
}
"""

ris_output = convert_bibtex_to_ris(bibtex_entry)
print(ris_output)
