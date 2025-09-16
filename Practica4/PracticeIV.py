import os
import pandas as pd
import spacy
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from collections import Counter
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier


#   Cargar el modelo de Spacy para español
nlp = spacy.load("es_core_news_sm")


#cargar el dataset
df = pd.read_csv("TA1C_dataset_detection_train.csv", encoding="utf-8")
assert 'Teaser Text' in df.columns and 'Tag Value' in df.columns, "Columnas esperadas no encontradas"

teaser_texts = df['Teaser Text'].tolist()
tag_values = df['Tag Value'].tolist()

#funcion para normalizar el texto
def normalize_text(text, remove_stopwords=True, remove_punct=True, remove_numbers=True, apply_lemmatization=True):
    doc = nlp(text)
    tokens = []
    for token in doc:
        if remove_stopwords and token.is_stop:
            continue
        if remove_punct and token.is_punct:
            continue
        if remove_numbers and token.like_num:
            continue
        if apply_lemmatization:
            tokens.append(token.lemma_.lower())
        else:
            tokens.append(token.text.lower())
    return " ".join(tokens)

#   combinaciones de normalización
normalizations = {
    "solo_lemas":        dict(remove_stopwords=False, remove_punct=False, remove_numbers=False, apply_lemmatization=True),
    "lemas_y_stopwords": dict(remove_stopwords=True, remove_punct=False, remove_numbers=False, apply_lemmatization=True),
    "limpieza_total":    dict(remove_stopwords=True, remove_punct=True, remove_numbers=True, apply_lemmatization=True),
    "sin_lemas":         dict(remove_stopwords=True, remove_punct=True, remove_numbers=True, apply_lemmatization=False),
}

normalized_versions = {}

for nombre, config in normalizations.items():
    print(f"→ Normalizando versión: {nombre}")
    normalized_versions[nombre] = [normalize_text(text, **config) for text in teaser_texts]



#   guardar los resultados
output_folder = "normalizaciones"
if os.path.exists(output_folder):
    print("La carpeta 'normalizaciones' ya existe. No se volverán a guardar los CSV.")
else:
    os.makedirs(output_folder)
    for nombre, textos in normalized_versions.items():
        output_df = pd.DataFrame({
            "Teaser Text": teaser_texts,
            "Tag Value": tag_values,
            "Teaser Normalizado": textos
        })
        filename = os.path.join(output_folder, f"{nombre}.csv")
        output_df.to_csv(filename, index=False, encoding="utf-8")
        print(f"Guardado: {filename}")


# función para dividir en train y dev
def split_train_dev(df_normalizado):
    X = df_normalizado["Teaser Normalizado"].tolist()
    y = df_normalizado["Tag Value"].tolist()
    X_train, X_dev, y_train, y_dev = train_test_split(
        X, y,
        test_size=0.25,
        shuffle=True,
        random_state=0,
        stratify=y
    )
    return X_train, X_dev, y_train, y_dev


#  division de train/dev

particiones = {}
for nombre, textos in normalized_versions.items():
    df_norm = pd.DataFrame({
        "Teaser Normalizado": textos,
        "Tag Value": tag_values
    })

    X_train, X_dev, y_train, y_dev = split_train_dev(df_norm)
    particiones[nombre] = {
        "X_train": X_train,
        "X_dev": X_dev,
        "y_train": y_train,
        "y_dev": y_dev
    }

    print(f"\nDivisión realizada para: {nombre}")
    print(f"Train: {Counter(y_train)}")
    print(f"Dev: {Counter(y_dev)}")


# Rango de n-gramas a probar
ngramas = {
    "unigramas": (1, 1),
    "bigramas": (2, 2),
    "trigramas": (3, 3),
    "uni_bi": (1, 2),
}

# Vectorizadores disponibles
vectorizers = {
    "tfidf": lambda ngram_range: TfidfVectorizer(ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b"),
    "frecuencia": lambda ngram_range: CountVectorizer(ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b"),
    "binario": lambda ngram_range: CountVectorizer(binary=True, ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b"),
}

# Carpeta de salida para los .pkl
vector_output_folder = "vectorizadores"
os.makedirs(vector_output_folder, exist_ok=True)

# Iterar sobre cada partición
for nombre_norm, datos in particiones.items():
    X_train = datos["X_train"]
    X_dev = datos["X_dev"]

    for ngrama_nombre, ngrama_range in ngramas.items():
        for vector_nombre, vector_func in vectorizers.items():
            nombre_combo = f"{nombre_norm}__{vector_nombre}__{ngrama_nombre}"

            # Crear y ajustar vectorizador
            vectorizador = vector_func(ngrama_range)
            X_train_vec = vectorizador.fit_transform(X_train)
            X_dev_vec = vectorizador.transform(X_dev)

            # Guardar el vectorizador en un archivo .pkl
            pkl_path = os.path.join(vector_output_folder, f"{nombre_combo}.pkl")
            with open(pkl_path, "wb") as f:
                pickle.dump(vectorizador, f)

            print(f"Guardado vectorizador: {pkl_path}")

# modelos y sus parámetros
parametros_modelos = {
    "NaiveBayes": {
        "model": MultinomialNB(),
        "params": {
            "alpha": [0.1, 0.5, 1.0]
        }
    },
    "LogisticRegression": {
        "model": LogisticRegression(max_iter=1000),
        "params": {
            "C": [0.1, 1.0, 10],
            "solver": ["liblinear"]
        }
    },
    "SVM": {
        "model": SVC(),
        "params": {
            "C": [0.1, 1.0, 10],
            "kernel": ["linear", "rbf"]
        }
    }
}



# grid search y cross validation
vector_folder = "vectorizadores"
resultados_grid = []

for nombre_norm, datos in particiones.items():
    X_raw = datos["X_train"]
    y_raw = datos["y_train"]

    for pkl_file in os.listdir(vector_folder):
        if not pkl_file.startswith(nombre_norm) or not pkl_file.endswith(".pkl"):
            continue

        path_vector = os.path.join(vector_folder, pkl_file)
        with open(path_vector, "rb") as f:
            vectorizador = pickle.load(f)

        X_vec = vectorizador.transform(X_raw)
        y = np.array(y_raw)

        for modelo_nombre, config in parametros_modelos.items():
            model = config["model"]
            params = config["params"]

            print(f"GridSearch → {modelo_nombre} | {pkl_file}")

            grid = GridSearchCV(
                estimator=model,
                param_grid=params,
                scoring="f1_macro",
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=0),
                n_jobs=-1
            )
            grid.fit(X_vec, y)

            resultados_grid.append({
                "Normalización": nombre_norm,
                "Vectorizador": pkl_file,
                "Modelo": modelo_nombre,
                "F1_macro": grid.best_score_,
                "Parámetros óptimos": grid.best_params_
            })

# Guardar resultados en CSV
df_grid = pd.DataFrame(resultados_grid)
df_grid.to_csv("resultados_gridsearch.csv", index=False)
print("Resultados guardados en: resultados_gridsearch.csv")



