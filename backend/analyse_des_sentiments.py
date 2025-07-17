#!/usr/bin/env python3
# predict_with_hf_model.py

from transformers import pipeline

# 1) Installez si besoin :
#    pip install transformers torch

# 2) Définissez la liste de modèles possibles
MODELS = [
    "SamLowe/roberta-base-go_emotions",
    "tabularisai/multilingual-sentiment-analysis",
    "j-hartmann/emotion-english-distilroberta-base",
    "cardiffnlp/twitter-roberta-base-emotion-multilabel-latest"
]

# 3) Choisissez le modèle à utiliser (ici GoEmotions)
selected_model = MODELS[0]

# 4) Créez la pipeline en récupérant toutes les étiquettes hzea zj
pipe = pipeline(
    "text-classification",
    model=selected_model,
    tokenizer=selected_model,
    #top_k= 3  #return_all_scores=True 
    return_all_scores=True
)


def predict_sentiment(text: str):
    # on récupère une liste de dicts : [{"label": "...", "score": ...}, ...]
    scores = pipe(text)[0]
    return scores

if __name__ == "__main__":
    tweet = input("Entrez un tweet à tester : ")
    scores = predict_sentiment(tweet)

    # Affichez tous les scores détaillés
    print("Scores détaillés :")
    for emo in scores:
        print(f"  {emo['label']}: {emo['score']:.2f}")

    # Sélectionnez la prédiction la plus élevée
    top = max(scores, key=lambda x: x["score"])
    print(f"\nPrédiction principale : {top['label']} (confiance : {top['score']:.2f})")


