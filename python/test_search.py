from .search_engine import SearchEngine
from .database import MedicalDatabase

# Charger la base de données
db = MedicalDatabase()
# Créer le moteur de recherche
engine = SearchEngine(db)
query = "j'ai des maux de tête et de la fièvre"
# Hybride (par défaut)
engine.set_mode("hybrid")
results_hybrid = engine.search(query)
print("\n=== Mode Hybride ===")
print("Symptômes extraits :", results_hybrid["extracted_entities"])
for r in results_hybrid["results"]:
    print(f"- {r['disease']} ({r['scorePercent']}%) -> Symptômes trouvés : {r['matchedSymptoms']}")
# Syntaxique
engine.set_mode("syntactic")
results_syntax = engine.search(query)
print("=== Mode Syntaxique ===")
print("Symptômes extraits :", results_syntax["extracted_entities"])
for r in results_syntax["results"]:
    print(f"- {r['disease']} ({r['scorePercent']}%) -> Symptômes trouvés : {r['matchedSymptoms']}")

# Sémantique
engine.set_mode("semantic")
results_sem = engine.search(query)
print("\n=== Mode Sémantique ===")
print("Symptômes extraits :", results_sem["extracted_entities"])
for r in results_sem["results"]:
    print(f"- {r['disease']} ({r['scorePercent']}%) -> Symptômes trouvés : {r['matchedSymptoms']}")






# Étape 0 : imports et setup
from .preprocessor import TextPreprocessor
from .database import MedicalDatabase

db = MedicalDatabase()       # Initialisation de la base médicale
tp = TextPreprocessor(db)    # Création du préprocesseur

# Étapes 1 → 4 : nettoyage, multi-mots, lemmatisation, synonymes
tokens = tp.tokenize("j'ai des maux de tête et de la fièvre")
print(tokens)