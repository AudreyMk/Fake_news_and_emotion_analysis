# 🧠 Fake News & Emotion Analysis on Bluesky Posts

Ce projet vise à détecter les **fake news** et analyser les **émotions** exprimées dans des publications du réseau social **Bluesky**, à l’aide de techniques de traitement automatique du langage naturel (NLP) et de modèles d’intelligence artificielle comme **BERT**.

---

## 📌 Objectifs

- Collecter des publications depuis Bluesky via l'API AT Protocol.
- Nettoyer et préparer les données textuelles.
- Analyser les sentiments (positif, négatif, neutre).
- Détecter les publications contenant de potentielles fausses informations (fake news).
- Mettre en place une pipeline de traitement automatisée.

---

## 🛠️ Technologies utilisées

- **Python**
- **FastAPI** – pour la création d'une API backend
- **psycopg / PostgreSQL (Neon)** – pour la base de données postgres
- **transformers (BERT)** – pour la classification des sentiments et fake news
- **pandas / NumPy / scikit-learn** - Pour le Fine-tuning BERT (Fake News) et traitement des datasets
- **AT Protocol SDK** – pour collecter des posts sur Bluesky
- **Render** – pour le déploiement de l’API

---

## 📂 Structure du projet

```
.
├── backend/                   # Backend FastAPI
│   ├── collector.py          # Récupération des posts Bluesky ((collecte aléatoire, collecte info user via le lien user, collecte d'un post unique via lien du post)
│   ├── db.py                 # Connexion et requêtes PostgreSQL
│   ├── backend.py            # API FastAPI
│   └── ...
├── bert_finetune.py          # Fine-tuning du modèle BERT
├── analyse_des_sentiments.py # Prédiction sentiment/fake news
├── test_getall_data.py       # Scripts de collecte des données sur Bluesky (collecte aléatoire, collecte info user via le lien user, collecte d'un post unique via lien du post)
├── final_model_bert/         # Modèle BERT fine-tuné
├── .env                      # Variables d’environnement (non versionné)
└── README.md
```

---

## 🚀 Lancer le projet en local

### 1. Cloner le repo

```bash
git clone https://github.com/AudreyMk/Fake_news_and_emotion_analysis.git
cd Fake_news_and_emotion_analysis
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` sous Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer un fichier `.env`

```env
BLUESKY_IDENTIFIER=...
BLUESKY_APP_PASSWORD=...
DB_URL=...
```

### 5. Lancer l’API

```bash
uvicorn backend.backend:app --reload
```

---

## 📊 Exemple de prédiction

Une fois l’API lancée, vous pouvez envoyer un JSON contenant un texte à analyser :

```json
{
  "text": "Le gouvernement va rendre tout gratuit dès demain !"
}
```

Et obtenir une réponse comme :

```json
{
  "sentiment": "négatif",
  "fake_news": true
}
```

---

## 📬 Contact

Pour toute question ou suggestion, vous pouvez me contacter via GitHub ou par email.

---

## 🛡️ Remarques

- Les clés API et identifiants ne sont pas versionnés et doivent être définis dans un fichier `.env`.
- Les modèles BERT fine-tunés sont stockés dans `final_model_bert/`.

---

## 📖 Auteurs

- Audrey Magne  
- [GitHub: @AudreyMk](https://github.com/AudreyMk)
