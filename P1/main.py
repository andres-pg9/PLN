import re

bibtex_entry = """
@inproceedings{10.1145/3627673.3679558,
author = {Sun, Zhongxiang and Si, Zihua and Zang, Xiaoxue and Zheng, Kai and Song, Yang and Zhang, Xiao and Xu, Jun},
title = {Large Language Models Enhanced Collaborative Filtering},
year = {2024},
isbn = {9798400704369},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3627673.3679558},
doi = {10.1145/3627673.3679558},
abstract = {Recent advancements in Large Language Models (LLMs) have attracted considerable interest among researchers to leverage these models to enhance Recommender Systems (RSs). Existing work predominantly utilizes LLMs to generate knowledge-rich texts or utilizes LLM-derived embeddings as features to improve RSs. Although the extensive world knowledge embedded in LLMs generally benefits RSs, the application can only take a limited number of users and items as inputs, without adequately exploiting collaborative filtering information. Considering its crucial role in RSs, one key challenge in enhancing RSs with LLMs lies in providing better collaborative filtering information through LLMs. In this paper, drawing inspiration from the in-context learning and chain of thought reasoning in LLMs, we propose the Large Language Models enhanced Collaborative Filtering (LLM-CF) framework, which distills the world knowledge and reasoning capabilities of LLMs into collaborative filtering. We also explored a concise and efficient instruction-tuning method, which improves the recommendation capabilities of LLMs while preserving their general functionalities (e.g., not decreasing on the LLM benchmark). Comprehensive experiments on three real-world datasets demonstrate that LLM-CF significantly enhances several backbone recommendation models and consistently outperforms competitive baselines, showcasing its effectiveness in distilling the world knowledge and reasoning capabilities of LLM into collaborative filtering.},
booktitle = {Proceedings of the 33rd ACM International Conference on Information and Knowledge Management},
pages = {2178–2188},
numpages = {11},
keywords = {collaborative filtering, large language models},
location = {Boise, ID, USA},
series = {CIKM '24}
}
"""

bibtex_entry2 = """
@inproceedings{10.1145/3678717.3691226,
author = {O'Sullivan, Kent and Schneider, Nicole R. and Samet, Hanan},
title = {Metric Reasoning in Large Language Models},
year = {2024},
isbn = {9798400711077},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3678717.3691226},
doi = {10.1145/3678717.3691226},
abstract = {Spatial reasoning is a particularly challenging task that requires inferring implicit information about objects based on their relative positions in space. In an effort to develop general purpose geo-foundation models that can perform a variety of spatial reasoning tasks, preliminary work has explored what kinds of world knowledge and spatial reasoning capabilities Large Language Models (LLMs) naturally inherit from their training data. Recent work suggests that LLMs contain geospatial knowledge in the form of understanding geo-coordinates and associating spatial meaning to the key terms "near" and "far." In this paper, we show that LLMs lack the ability to adapt the meaning of the words "near" and "far" to the appropriate scale when provided contextual reference points. By uncovering biases in how LLMs answer distance-related spatial questions, we set the groundwork for developing new techniques that may enable LLMs to perform accurate spatial reasoning.},
booktitle = {Proceedings of the 32nd ACM International Conference on Advances in Geographic Information Systems},
pages = {501–504},
numpages = {4},
keywords = {Large language models, geo-foundation models, metric relations},
location = {Atlanta, GA, USA},
series = {SIGSPATIAL '24}
}
"""


bibtex_entry3 = """
@article{10.1145/3703403,
author = {Sundar, Varun and Gupta, Mohit},
title = {Quanta Computer Vision},
year = {2025},
issue_date = {Winter 2024},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
volume = {31},
number = {2},
issn = {1528-4972},
url = {https://doi.org/10.1145/3703403},
doi = {10.1145/3703403},
abstract = {Light impinges on a camera's sensor as a collection of discrete quantized elements, or photons. An emerging class of devices, called single-photon sensors, offers the unique capability of detecting individual photons with high-timing precision. With the increasing accessibility of high-resolution single-photon sensors, we can now explore what computer vision would look like if we could operate on light, one photon at a time.},
journal = {XRDS},
month = jan,
pages = {38–43},
numpages = {6}
}
"""

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
    "ID": "ID",
    "@article": "TY  - JOUR",
    "@inproceedings": "TY  - CONF",
}

def clean_text(text):
    text = re.sub(r'{\\([a-zA-Z])}', r'\1', text)
    text = re.sub(r'[{}]', '', text)
    return text.strip()

def split_authors(authors_str):
    authors = re.split(r'\s+and\s+', authors_str.strip())  # Divide por 'and'
    return [clean_text(author.strip()) for author in authors]

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

    ris_entries.append("ER  -")

    return "\n".join(ris_entries)

ris_output = convert_bibtex_to_ris(bibtex_entry3)
print(ris_output)
