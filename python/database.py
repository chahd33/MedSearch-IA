"""
MedSearch IA — Base de données médicale locale optimisée avec indexation TF-IDF.

CORRECTIONS v2 :
  - norm() extraite en fonction module-level et importable par similarity.py et
    preprocessor.py → plus de triple implémentation identique.
  - _build_index() précalcule tous les vecteurs TF-IDF dans self._disease_vectors.
  - get_disease_vector() est maintenant O(1) (simple lookup dict).
  - MedicalDatabase._norm() conservé comme alias statique pour la compatibilité
    interne (SyntacticSimilarity l'appelle via self.db._norm()).
"""

import math
import unicodedata
from .exceptions import DatabaseError
from .data import MedicalData


# ------------------------------------------------------------------
# Fonction de normalisation partagée (SOURCE UNIQUE DE VÉRITÉ)
# Importée par similarity.py et preprocessor.py pour éviter les trois implémentations dupliquées.

def norm(term: str) -> str:
    """
    Normalise un terme : minuscules, accents retirés (NFD→ASCII)et nettoyage des espaces.
    """
    return (
        unicodedata.normalize("NFD", term.lower().strip())
        .encode("ascii", "ignore")
        .decode("ascii")
    )


class MedicalDatabase:
    """Base locale indexée avec TF-IDF, optimisée pour recherches rapides."""

    # Alias statique pour la compatibilité avec SyntacticSimilarity
    # qui appelle self.db._norm(). Délègue à la fonction module-level.
    @staticmethod
    def _norm(term: str) -> str:
        return norm(term)

    def __init__(self):
        self.diseases: list[dict] = []
        self.vocabulary: set[str] = set()
        self.idf: dict[str, float] = {}
        self.symptom_to_diseases: dict[str, list[int]] = {}
        self.norm_to_original: dict[str, str] = {}
        self.categories: dict[str, list[str]] = {}
        self.synonyms: dict[str, list[str]] = {}

        # Mappings optimisés
        self.norm_symptom_to_category: dict[str, str] = {}
        self.norm_synonym_to_canonical: dict[str, str] = {}

        # FIX : cache des vecteurs TF-IDF précalculés {disease_id: vector}
        self._disease_vectors: dict[int, dict[str, float]] = {}

        self._load()

    def _load(self) -> None:
        try:
            self.diseases = MedicalData.get_diseases()
            self.synonyms = MedicalData.get_synonyms()
            self.categories = MedicalData.get_categories()
            if not self.diseases:
                raise DatabaseError("La base de données est vide")
            self._build_index()
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur lors du chargement : {e}") from e

    def _build_index(self) -> None:
        n = len(self.diseases)

        # Construction vocabulaire, mapping symptôme → maladies, tf bruts
        # On mémorise aussi les tf par maladie pour le cache vecteurs
        raw_tf: dict[int, dict[str, int]] = {}

        for disease in self.diseases:
            did = disease["id"]
            raw_tf[did] = {}
            for symptom in disease["symptoms"]:
                key = self._norm(symptom)
                self.vocabulary.add(key)
                self.symptom_to_diseases.setdefault(key, []).append(did)
                raw_tf[did][key] = raw_tf[did].get(key, 0) + 1
                if key not in self.norm_to_original:
                    self.norm_to_original[key] = symptom

        # Calcul IDF
        for term in self.vocabulary:
            df = len(self.symptom_to_diseases.get(term, []))
            self.idf[term] = math.log((n + 1) / (df + 1)) + 1

        # FIX : précalcul des vecteurs TF-IDF → get_disease_vector() = O(1)
        for disease in self.diseases:
            did = disease["id"]
            self._disease_vectors[did] = {
                key: freq * self.idf[key]
                for key, freq in raw_tf[did].items()
                if key in self.idf
            }

        # Mapping symptôme → catégorie (pré-calculé)
        for cat, symptoms in self.categories.items():
            for s in symptoms:
                key = self._norm(s)
                self.norm_symptom_to_category[key] = cat

        # Mapping synonyme normalisé → canonical
        for canonical, syns in self.synonyms.items():
            norm_canonical = self._norm(canonical)
            self.norm_synonym_to_canonical[norm_canonical] = norm_canonical
            for syn in syns:
                self.norm_synonym_to_canonical[self._norm(syn)] = norm_canonical

    def get_disease_vector(self, disease_id: int) -> dict[str, float]:
        """
        Retourne le vecteur TF-IDF d'une maladie.
        O(1) — lookup dans le cache précalculé à l'indexation.
        """
        if disease_id not in self._disease_vectors:
            raise DatabaseError(f"Maladie {disease_id} introuvable")
        return self._disease_vectors[disease_id]

    def get_query_vector(self, tokens: list[str]) -> dict[str, float]:
        tf: dict[str, float] = {}

        for token in tokens:
            key = self._norm(token)
            if key in self.idf:
                tf[key] = tf.get(key, 0) + 1
            elif key in self.norm_synonym_to_canonical:
                canonical = self.norm_synonym_to_canonical[key]
                if canonical in self.idf:
                    tf[canonical] = tf.get(canonical, 0) + 1
            else:
                # Substring fallback
                for vocab_key in self.vocabulary:
                    if key in vocab_key or vocab_key in key:
                        tf[vocab_key] = tf.get(vocab_key, 0) + 0.8

        # Expansion par synonymes (bonus 0.5)
        # Note : le double-comptage "toux persistante" est résolu dans data.py
        # (retiré des synonymes), donc cette expansion est maintenant sûre.
        added = {}
        for k in list(tf.keys()):
            canonical = self.norm_synonym_to_canonical.get(k)
            if canonical and canonical != k:
                added[canonical] = added.get(canonical, 0) + 0.5

        for k, v in added.items():
            tf[k] = tf.get(k, 0) + v

        # TF × IDF
        return {key: freq * self.idf[key] for key, freq in tf.items() if key in self.idf}

    def find_similar_symptoms(self, input_text: str) -> list[dict]:
        if not input_text or len(input_text) < 2:
            return []

        norm_input = self._norm(input_text)
        results, seen = [], set()

        # Exact / substring match
        for norm_sym in self.vocabulary:
            if norm_input in norm_sym or norm_sym.startswith(norm_input):
                if norm_sym not in seen:
                    seen.add(norm_sym)
                    results.append({
                        "symptom": self.norm_to_original.get(norm_sym, norm_sym),
                        "category": self._get_category(norm_sym),
                        "type": "exact",
                    })

        # Synonym match
        for syn_norm, canonical in self.norm_synonym_to_canonical.items():
            if norm_input in syn_norm or syn_norm.startswith(norm_input):
                if canonical not in seen:
                    seen.add(canonical)
                    results.append({
                        "symptom": self.norm_to_original.get(canonical, canonical),
                        "category": self._get_category(canonical),
                        "type": "synonym",
                    })

        return results[:8]

    def _get_category(self, norm_symptom: str) -> str:
        return self.norm_symptom_to_category.get(norm_symptom, "autre")

    @property
    def stats(self) -> dict:
        return {"diseases": len(self.diseases), "symptoms": len(self.vocabulary)}