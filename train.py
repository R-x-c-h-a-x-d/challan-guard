"""Train baseline ML model: TF-IDF (word + char n-grams) + Logistic Regression."""
import joblib, pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

df = pd.read_csv("data/sms.csv")
X_tr, X_te, y_tr, y_te = train_test_split(df.text, df.label, test_size=0.2,
                                          stratify=df.label, random_state=42)
word = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=2)
char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, min_df=2)
Xtr = hstack([word.fit_transform(X_tr), char.fit_transform(X_tr)])
Xte = hstack([word.transform(X_te), char.transform(X_te)])

clf = LogisticRegression(max_iter=1000, class_weight="balanced").fit(Xtr, y_tr)
pred = clf.predict(Xte)
print(classification_report(y_te, pred, target_names=["safe", "scam"]))
print("confusion matrix:\n", confusion_matrix(y_te, pred))
joblib.dump({"word": word, "char": char, "clf": clf}, "models/sms_model.joblib")
print("saved models/sms_model.joblib")