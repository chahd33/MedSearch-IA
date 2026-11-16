# 🩺 MedSearch IA

**Moteur de recherche médical intelligent** permettant de suggérer des pathologies potentielles à partir de symptômes décrits en langage naturel, à l'écrit ou à la voix.

🎓 **Projet académique — Avril 2026 | ISSAT Sousse**

> ⚠️ Ce projet est réalisé à des fins académiques et informatives. Il ne remplace pas un avis ou un diagnostic médical professionnel.

## ✨ Fonctionnalités

- Saisie des symptômes en langage naturel (français).
- Saisie vocale grâce à la Web Speech API.
- Trois modes de recherche : syntaxique (TF-IDF), sémantique et hybride.
- Suggestions de symptômes pendant la saisie.
- Affichage des 5 pathologies les plus pertinentes avec leurs scores.
- Liens vers des sources d'informations médicales fiables.

## 🧠 Approche technique

Le système analyse les symptômes saisis grâce à des techniques de traitement du langage naturel (NLP), puis les compare à une base de connaissances médicales.

Principales approches utilisées :
- Prétraitement du texte et extraction des symptômes.
- TF-IDF et similarité cosinus.
- Ontologie des symptômes et embeddings.
- Combinaison de scores pour classer les résultats.

## 🛠️ Technologies utilisées

- **Backend :** Python, Flask, Flask-CORS.
- **IA / NLP :** TF-IDF, Sentence Transformers, embeddings, NumPy, PyTorch.
- **Frontend :** HTML, CSS, JavaScript, Web Speech API.

## 📁 Structure du projet

- `python/` : Backend, traitement NLP et moteur de recherche.
- `static/` : Fichiers CSS et JavaScript.
- `templates/` : Interface web.
- `docs/` : Documentation et captures d'écran.

## 🚀 Installation et lancement

**Prérequis :** Python 3.10 ou supérieur.

```bash
git clone https://github.com/chahd33/MedSearch-IA.git
cd MedSearch-IA

python -m venv venv
pip install -r requirements.txt

python -m python.app
```

Accéder à l'application via : `http://127.0.0.1:5000`

## ⚠️ Limites

- Base de connaissances limitée à 35 pathologies.
- Prise en charge du français uniquement.
- Les résultats sont des suggestions et non des diagnostics médicaux.
- Absence d'évaluation quantitative sur un jeu de test annoté.

## 👤 Auteur

**Chahd** — Étudiante en informatique, spécialité Génie Logiciel, ISSAT Sousse.

[LinkedIn](https://www.linkedin.com/in/chahd-belkahla-0aa058331) · [GitHub](https://github.com/chahd33)
