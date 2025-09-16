import os
import re
import pickle
import numpy as np
import pandas as pd
import spacy
from collections import Counter
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report
from imblearn.over_sampling import RandomOverSampler
from sklearn.metrics import classification_report, f1_score


# Cargar modelo de spaCy
nlp = spacy.load("es_core_news_sm")

# CARGA Y LIMPIEZA DE DATOS
df = pd.read_csv("TA1C_dataset_detection_train.csv", encoding="utf-8")
assert 'Teaser Text' in df.columns and 'Tag Value' in df.columns

teaser_texts = df['Teaser Text'].tolist()
tag_values = df['Tag Value'].tolist()

def limpieza_ligera(texto):
    texto = texto.lower()
    texto = re.sub(r"http\S+", "", texto)  # eliminar URLs
    texto = re.sub(r"[^\w\s\"#]", "", texto)  # conservar comillas y hashtags
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

print("→ Aplicando limpieza ligera...")
textos_limpios = [limpieza_ligera(text) for text in teaser_texts]

# GUARDAR NORMALIZADO
os.makedirs("normalizaciones", exist_ok=True)
df_output = pd.DataFrame({
    "Teaser Text": teaser_texts,
    "Tag Value": tag_values,
    "Teaser Normalizado": textos_limpios
})
df_output.to_csv("normalizaciones/limpieza_ligera.csv", index=False, encoding="utf-8")

# === DIVISIÓN TRAIN/DEV ===
df_norm = pd.DataFrame({
    "Teaser Normalizado": textos_limpios,
    "Tag Value": tag_values
})

X_train, X_dev, y_train, y_dev = train_test_split(
    df_norm["Teaser Normalizado"].tolist(),
    df_norm["Tag Value"].tolist(),
    test_size=0.25,
    stratify=tag_values,
    random_state=0
)

particiones = {
    "limpieza_ligera": {
        "X_train": X_train,
        "X_dev": X_dev,
        "y_train": y_train,
        "y_dev": y_dev
    }
}

#  VECTORIZACIÓN
ngramas = {
    "unigramas": (1, 1),
    "bigramas": (2, 2),
    "trigramas": (3, 3),
    "uni_bi": (1, 2),
    "uni_tri": (1,3)

}

vectorizers = {
    "tfidf": lambda ngram_range: TfidfVectorizer(ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b"),
    "frecuencia": lambda ngram_range: CountVectorizer(ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b"),
    "binario": lambda ngram_range: CountVectorizer(binary=True, ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b"),
}

os.makedirs("vectorizadores", exist_ok=True)

for nombre_norm, datos in particiones.items():
    for ngrama_nombre, ngrama_range in ngramas.items():
        for vector_nombre, vector_func in vectorizers.items():
            nombre_combo = f"{nombre_norm}__{vector_nombre}__{ngrama_nombre}"
            vectorizador = vector_func(ngrama_range)
            X_train_vec = vectorizador.fit_transform(datos["X_train"])
            pkl_path = os.path.join("vectorizadores", f"{nombre_combo}.pkl")
            with open(pkl_path, "wb") as f:
                pickle.dump(vectorizador, f)
            print(f"Guardado vectorizador: {pkl_path}")

# modelos
parametros_modelos = {
    "NaiveBayes": {
        "model": MultinomialNB(),
        "params": {"alpha": [0.1, 0.5, 1.0]}
    },
    "LogisticRegression": {
        "model": LogisticRegression(max_iter=1000),
        "params": {"C": [0.1, 1.0, 10], "solver": ["liblinear"]}
    },
    "SVM": {
        "model": SVC(),
        "params": {"C": [0.1, 1.0, 10], "kernel": ["linear", "rbf"]}
    },

}


# GRID SEARCH + OVERSAMPLING + EVALUACIÓN
resultados_grid = []

for nombre_norm, datos in particiones.items():
    X_raw = datos["X_train"]
    y_raw = datos["y_train"]

    for pkl_file in os.listdir("vectorizadores"):
        if not pkl_file.startswith(nombre_norm) or not pkl_file.endswith(".pkl"):
            continue

        with open(os.path.join("vectorizadores", pkl_file), "rb") as f:
            vectorizador = pickle.load(f)

        X_vec = vectorizador.transform(X_raw)
        y = np.array(y_raw)

        # Oversampling
        ros = RandomOverSampler(random_state=0)
        X_resampled, y_resampled = ros.fit_resample(X_vec, y)

        for modelo_nombre, config in parametros_modelos.items():
            print(f"\nGridSearch → {modelo_nombre} | {pkl_file}")
            grid = GridSearchCV(
                estimator=config["model"],
                param_grid=config["params"],
                scoring="f1_macro",
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=0),
                n_jobs=-1
            )
            grid.fit(X_resampled, y_resampled)

            # Evaluar en dev
            X_dev_vec = vectorizador.transform(datos["X_dev"])
            y_pred = grid.best_estimator_.predict(X_dev_vec)

            # Imprimir reporte de clasificación
            print(classification_report(datos["y_dev"], y_pred, digits=4))

            # Calcular F1 macro manualmente
            f1_macro_dev = f1_score(datos["y_dev"], y_pred, average="macro")
            print(f"F1-macro: {f1_macro_dev:.4f}")

            resultados_grid.append({
            "Normalización": nombre_norm,
            "Vectorizador": pkl_file,
            "Modelo": modelo_nombre,
            "F1_macro_DEV": f1_macro_dev,     # f1_macro real en conjunto dev
            "Parámetros óptimos": grid.best_params_
            })

# === GUARDAR RESULTADOS ===
df_resultados = pd.DataFrame(resultados_grid)
df_resultados.to_csv("resultados_gridsearch.csv", index=False)
print("Resultados guardados en: resultados_gridsearch.csv")
