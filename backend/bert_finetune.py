from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re

# 1. Charger modèle et tokenizer
model_path = "./final_model_bert"  # Chemin vers ton dossier local
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path, trust_remote_code=True)
model.eval()

# 2. Fonction de prédiction
def predict(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        prediction = torch.argmax(logits, dim=1).item()
    return prediction

# 3. Exemple
tweet = "La france est un pays d'Afrique."
label = predict(tweet)
print(f"Label prédit : {label}")



# --- 1. Configuration et chargement du modèle ---

# Chemin où vous avez sauvegardé votre modèle et tokenizer
# ASSUREZ-VOUS QUE CE CHEMIN EST CORRECT !
MODEL_PATH = "./final_model_bert"

# Définir le périphérique (GPU si disponible, sinon CPU)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Utilisation du périphérique : {DEVICE}")

# Charger le tokenizer et le modèle
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(DEVICE)
    model.eval() # Mettre le modèle en mode évaluation (désactive dropout, etc.)
    print("Modèle et tokenizer chargés avec succès !")
except Exception as e:
    print(f"Erreur lors du chargement du modèle ou du tokenizer : {e}")
    print("Vérifiez que le chemin MODEL_PATH est correct et que les fichiers existent.")
    exit() # Quitter si le chargement échoue

# Assurez-vous que le modèle a des mappings de labels si vous les avez sauvegardés
# Si vous n'avez pas de config.json avec id2label, vous devrez les définir manuellement
# basés sur votre mapping original.
# Par exemple, si 0 correspond à 'négatif' et 1 à 'positif'
if hasattr(model.config, 'id2label'):
    model.config.id2label = {0: 'Faux', 1: 'Vrai'}
    int_to_label = model.config.id2label
    print("id2label du modèle :", model.config.id2label)
else:
    print("Attention : `id2label` non trouvé dans la configuration du modèle. Utilisation des labels par défaut (0, 1).")
    # Remplacez ceci par vos vrais labels si vous les connaissez (ex: {0: 'non_rouge', 1: 'rouge'})
    int_to_label = {0: 'Faux', 1: 'Vrai'} # Adaptez ceci à vos labels réels

# --- 2. Fonction de nettoyage de tweet (identique à celle utilisée pour l'entraînement) ---
def clean_tweet(text):
    text = re.sub(r"http\S+|www\S+", "<URL>", text)
    text = re.sub(r"@\w+", "<USER>", text)
    text = re.sub(r"#(\w+)", r"<HASHTAG> \1", text)
    return text.strip()

# --- 3. Fonction de prédiction ---
def predict_tweet(text):
    # Nettoyage du tweet
    cleaned_text = clean_tweet(text)

    # Tokenisation
    encoding = tokenizer(
        cleaned_text,
        add_special_tokens=True,
        max_length=128, # Utilisez la même MAX_LEN que pendant l'entraînement
        return_attention_mask=True,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    )

    input_ids = encoding['input_ids'].to(DEVICE)
    attention_mask = encoding['attention_mask'].to(DEVICE)

    # Prédiction
    with torch.no_grad(): # Pas besoin de calculer les gradients pour l'inférence
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        predicted_class_id = torch.argmax(probabilities, dim=1).item()

    # Traduire l'ID de classe en label lisible
    #predicted_label = int_to_label.get(predicted_class_id, f"Inconnu ({predicted_class_id})")

    prob_array = probabilities[0].cpu().numpy()
    proba_diff = abs(prob_array[0] - prob_array[1])

    if proba_diff < 0.15:
        final_label = "Opinion personnelle"
    else:
        final_label = int_to_label.get(predicted_class_id, f"Inconnu ({predicted_class_id})")

    return final_label, prob_array


    # Retourner les résultats
    #return predicted_label, probabilities[0].cpu().numpy()



# --- 5. Test interactif (optionnel) ---
print("\n--- Mode de test interactif ---")
print("Tapez 'quitter' pour sortir.")

while True:
    user_tweet = input("Entrez un tweet à analyser : ")
    if user_tweet.lower() == 'quitter':
        print("Fin du mode interactif.")
        break
    if not user_tweet.strip():
        print("Veuillez entrer un tweet.")
        continue

    label, probs = predict_tweet(user_tweet)
    print(f"  Prédiction : {label}")
    print(f"  Probabilités : {probs}")
    # for j, prob in enumerate(probs):
    #     print(f"    {int_to_label.get(j, f'label_{j}')}: {prob:.4f}")