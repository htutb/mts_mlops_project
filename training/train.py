import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("train.csv")
df = df[["comment_text", "toxic"]]
df["comment_text"] = df["comment_text"].fillna("").astype(str)
df = df[df["toxic"].isin([0, 1])]

X_train = df["comment_text"]
y_train = df["toxic"]

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=30000,
        ngram_range=(1, 3),
        min_df=2
    )),
    ("clf", LogisticRegression(
        max_iter=1500,
        class_weight="balanced",
        n_jobs=-1
    ))
])

pipeline.fit(X_train, y_train)
joblib.dump(pipeline, "ml_worker/model/model_pipeline.joblib")