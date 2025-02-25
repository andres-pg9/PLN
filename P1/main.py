import re
import pandas as pd

def load_equivalences(csv_path):
    """Carga las equivalencias de etiquetas desde el archivo CSV."""
    df = pd.read_csv(csv_path)
    return dict(zip(df['BibTeX Field'], df['RIS Tag']))

def bibtex_to_ris(bibtex_text, equivalences):
    """Convierte un texto en formato BibTeX a RIS."""
    ris_lines = ["TY  - CONF"]  # Tipo de referencia para conferencias
    
    for key, ris_tag in equivalences.items():
        pattern = rf"{key}\s*=\s*\{{(.*?)\}}"
        match = re.search(pattern, bibtex_text, re.DOTALL)
        if match:
            value = match.group(1)
            
            if key == "author":
                authors = value.split(" and ")
                for author in authors:
                    ris_lines.append(f"AU  - {author.strip()}")
            elif key == "editor":
                editors = value.split(" and ")
                for editor in editors:
                    ris_lines.append(f"ED  - {editor.strip()}")
            elif key == "pages":
                pages = value.split("--")
                ris_lines.append(f"SP  - {pages[0].strip()}")
                if len(pages) > 1:
                    ris_lines.append(f"EP  - {pages[1].strip()}")
            elif key == "address":
                ris_lines.append(f"CY  - {value.strip()}")
            elif key == "isbn":
                ris_lines.append(f"SN  - {value.strip()}")
            else:
                ris_lines.append(f"{ris_tag}  - {value.strip()}")
    
    match = re.match(r"@\w+\{(.*?),", bibtex_text)
    if match:
        ris_lines.append(f"ID  - {match.group(1).strip()}")
    
    ris_lines.append("ER  -")  # Fin del registro
    return "\n".join(ris_lines)

def ris_to_bibtex(ris_text, equivalences):
    """Convierte un texto en formato RIS a BibTeX."""
    bibtex_lines = ["@InProceedings{"]
    fields = {}
    
    for line in ris_text.split("\n"):
        match = re.match(r"(\w{2})  - (.*)", line)
        if match:
            ris_tag, value = match.groups()
            if ris_tag in equivalences.values():
                bib_key = [key for key, tag in equivalences.items() if tag == ris_tag][0]
                if bib_key == "author":
                    fields.setdefault("author", []).append(value)
                elif bib_key == "editor":
                    fields.setdefault("editor", []).append(value)
                elif bib_key == "pages":
                    if "pages" in fields:
                        fields["pages"] += f"--{value}"
                    else:
                        fields["pages"] = value
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
bibtex_example = """@InProceedings{10.1007/978-3-031-44693-1_30,
author={Huang, Hui and Wu, Shuangzhi and Liang, Xinnian and Wang, Bing and Shi, Yanrui and Wu, Peihao and Yang, Muyun and Zhao, Tiejun},
editor={Liu, Fei and Duan, Nan and Xu, Qingting and Hong, Yu},
title={Towards Making the Most of LLM for Translation Quality Estimation},
booktitle={Natural Language Processing and Chinese Computing},
year={2023},
publisher={Springer Nature Switzerland},
address={Cham},
pages={375--386},
isbn={978-3-031-44693-1}
} """

ris_output = bibtex_to_ris(bibtex_example, equivalences)
print("\n--- RIS OUTPUT ---\n", ris_output)
