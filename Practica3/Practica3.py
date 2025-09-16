#============ Bibliotecas necesarias ================
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report
# Import Pipeline
from sklearn.pipeline import Pipeline # Importing the Pipeline class

# Cargar el corpus de arxiv
df = pd.read_csv("arxiv_normalized_corpus.csv", delimiter="\t", encoding="utf-8")

# QUEDARSE SOLO CON LA PRIMERA CATEGORÍA EN 'Section'
df['section'] = df['Section'].apply(lambda x: x.split(',')[0].strip())


# Concatenar el título y el resumen para crear una sola columna de texto
df['text'] = df['Title'].fillna('') + ' ' + df['Abstract'].fillna('')

print(df[['Title', 'Abstract', 'text', 'section']].head(5))


# Definir las etiquetas y el texto
X = df['text']          # Entradas (título + resumen)
y = df['section']       # Salida (sección)



# Dividir el conjunto de datos en entrenamiento y prueba (80% entrenamiento, 20% prueba)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True, random_state=0)


# Vectorizar el texto utilizando TF-IDF, binary o frequency
vectorizers = {
    'tfidf': TfidfVectorizer(),
    'binary': CountVectorizer(binary=True),
    'frequency': CountVectorizer()
}


# Definir los clasificadores
models = {
    'Naive Bayes': MultinomialNB(),
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'SVM': SVC(),
    'MLP': MLPClassifier(max_iter=1000)
}

for vect_name, vectorizer in vectorizers.items():
    for model_name, model in models.items():
        print(f"\nUsing Vectorizer: {vect_name} | Classifier: {model_name}")
        pipe = Pipeline([
            ('text_representation', vectorizer),
            ('classifier', model)
        ])
        pipe.fit(X_train, y_train)

        # Print number of features (if supported)
        try:
            print(f"Number of features: {len(pipe['text_representation'].get_feature_names_out())}")
        except AttributeError:
            print("This vectorizer does not support get_feature_names_out")

        # Predict and evaluate
        y_pred = pipe.predict(X_test)
        print(classification_report(y_test, y_pred))





