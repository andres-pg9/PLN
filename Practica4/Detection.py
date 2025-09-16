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
from sklearn.metrics import classification_report, f1_score

# Cargar modelo spaCy
nlp = spacy.load("es_core_news_sm")

# Limpieza ligera
def limpieza_ligera(texto):
    texto = texto.lower()
    texto = re.sub(r"http\S+", "", texto)
    texto = re.sub(r"[^\w\s\"#]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

# Cargar datasets
df_train = pd.read_csv("TA1C_dataset_detection_train.csv", encoding="utf-8")
df_dev = pd.read_csv("TA1C_dataset_detection_dev.csv", encoding="utf-8")

# Preprocesamiento
X_train_raw = df_train["Teaser Text"].apply(limpieza_ligera).tolist()
y_train_raw = df_train["Tag Value"].tolist()
X_test_raw = df_dev["Teaser Text"].apply(limpieza_ligera).tolist()
tweet_ids = df_dev["Tweet ID"].tolist()

# Vectorización binaria con unigramas
vectorizador = CountVectorizer(binary=True, ngram_range=(1, 1), token_pattern=r"(?u)\b\w+\b")
X_train_vec = vectorizador.fit_transform(X_train_raw)
X_test_vec = vectorizador.transform(X_test_raw)

# Entrenar modelo: Logistic Regression con C=10 y solver liblinear
modelo = LogisticRegression(C=10, solver="liblinear", max_iter=1000)
modelo.fit(X_train_vec, y_train_raw)

# Predecir en el conjunto de test
y_pred_test = modelo.predict(X_test_vec)

# Guardar predicciones en formato solicitado
df_salida = pd.DataFrame({
    "Tweet ID": tweet_ids,
    "Tag Value": y_pred_test
})
df_salida.to_csv("detection.csv", index=False, encoding="utf-8")
print("Archivo 'detection.csv' generado.")
