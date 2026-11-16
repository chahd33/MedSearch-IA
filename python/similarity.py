import math
from abc import ABC, abstractmethod
from typing import Tuple, List
from .exceptions import SimilarityError
from .database import MedicalDatabase, norm

CRITICAL_SYMPTOMS = {"fievre", "toux", "difficultes respiratoires", "essoufflement"}


class SimilarityCalculator(ABC):
    def __init__(self, db: MedicalDatabase):
        if not db:
            raise SimilarityError("Base de données requise")
        self.db = db

    @abstractmethod
    def calculate(self, query_tokens: list[str], disease: dict) -> Tuple[float, List[str], List[str]]:
        """Retourne (score, symptômes_trouvés, symptômes_non_trouvés)"""
        pass

    def _cosine(self, a: dict, b: dict) -> float:
        dot = sum(a[k] * b[k] for k in a if k in b)
        norm_a = math.sqrt(sum(v * v for v in a.values())) or 1.0
        norm_b = math.sqrt(sum(v * v for v in b.values())) or 1.0
        return dot / (norm_a * norm_b)


from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import ClassVar, Tuple, List

_EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_EMBED_FALLBACK_THRESHOLD = 0.0   # on déclenche DrBERT seulement si règles == 0.0
_EMBED_SIM_FLOOR         = 0.15   # en dessous → on ignore le score embedding
_EMBED_SIM_CEIL          = 0.85   # plafond pour ne pas écraser les règles

_SIM_SYNONYM    = 0.90
_SIM_SAME_CAT   = 0.50
_SIM_BROAD_CAT  = 0.35
_SIM_SUBSTRING  = 0.40
_VISUAL_MIN_SIM = 0.85
_CRITICAL_BOOST = 0.15
_MIN_SUBSTR_LEN = 4


class SemanticSimilarity(SimilarityCalculator):
    _BROAD_CATEGORIES: ClassVar[frozenset[str]] = frozenset(
        {"general", "respiratoire", "digestif"}
    )

    def __init__(self, db: MedicalDatabase):
        super().__init__(db)
        self._syn_map = self._build_synonym_map()
        self._cat_map = self._build_category_map()
        self._embed_model: SentenceTransformer | None = None  # lazy load


    def _get_embed_model(self) -> SentenceTransformer:
        if self._embed_model is None:
            print(f"[SemanticSimilarity] Chargement de {_EMBED_MODEL_NAME}...")
            self._embed_model = SentenceTransformer(_EMBED_MODEL_NAME)
        return self._embed_model

    @lru_cache(maxsize=2048)
    def _embed(self, text: str) -> tuple[float, ...]:
        """Retourne l'embedding d'un texte (caché pour éviter les recalculs)."""
        vec = self._get_embed_model().encode(text, normalize_embeddings=True)
        return tuple(vec)  # tuple = hashable pour lru_cache

    def _cosine(self, a: str, b: str) -> float:
        """Cosine similarity entre deux termes via DrBERT."""
        va = np.array(self._embed(a))
        vb = np.array(self._embed(b))
        return float(np.dot(va, vb))  # déjà normalisés → dot = cosine

    # ------------------------------------------------------------------
    # Règles heuristiques (inchangées)
    # ------------------------------------------------------------------
    def _build_synonym_map(self) -> dict[str, set[str]]:
        from .data import MedicalData
        syn_map = {}
        for key, syns in MedicalData.get_synonyms().items():
            group = {norm(key)} | {norm(s) for s in syns}
            for term in group:
                syn_map[term] = group
        return syn_map

    def _build_category_map(self) -> dict[str, str]:
        from .data import MedicalData
        cat_map = {}
        for cat, symptoms in MedicalData.get_categories().items():
            for s in symptoms:
                cat_map[norm(s)] = cat
        return cat_map

    def _rule_similarity(self, a: str, b: str) -> float:
        """Similarité par règles uniquement (ex-_symptom_similarity)."""
        if a == b:
            return 1.0
        if b in self._syn_map.get(a, set()):
            return _SIM_SYNONYM
        cat_a, cat_b = self._cat_map.get(a), self._cat_map.get(b)
        if cat_a and cat_a == cat_b:
            return _SIM_BROAD_CAT if cat_a in self._BROAD_CATEGORIES else _SIM_SAME_CAT
        if a in b or b in a:
            return _SIM_SUBSTRING
        return 0.0

    # ------------------------------------------------------------------
    # Similarité hybride : règles → fallback si score == 0.0
    # ------------------------------------------------------------------
    def _symptom_similarity(self, a: str, b: str) -> float:
        rule_score = self._rule_similarity(a, b)

        if rule_score > _EMBED_FALLBACK_THRESHOLD:
            return rule_score  # les règles ont répondu → on s'arrête là

        cosine = self._cosine(a, b)

        # On ignore les similarités trop faibles (bruit)
        if cosine < _EMBED_SIM_FLOOR:
            return 0.0

        # On plafonne pour rester sous les scores des règles (0.35+)
        return round(min(cosine, _EMBED_SIM_CEIL) * _SIM_BROAD_CAT, 4)
        # ex : cosine=0.80 → 0.80 * 0.35 = 0.28  (contribue au score mais reste discret)

    # ------------------------------------------------------------------
    # Match visuel : utilise _symptom_similarity (règles + embedding)
    # pour cocher correctement même les synonymes et variantes proches.
    # ------------------------------------------------------------------
    def _is_visual_match(self, norm_ds: str, query_tokens: list[str]) -> bool:
        best_sim = max(
            (self._symptom_similarity(qt, norm_ds) for qt in query_tokens), default=0.0
        )
        if best_sim >= _SIM_BROAD_CAT:
            return True
        return any(
            qt in norm_ds or norm_ds in qt
            for qt in query_tokens
            if len(qt) >= _MIN_SUBSTR_LEN
        )

    # ------------------------------------------------------------------
    # Score principal
    # ------------------------------------------------------------------
    def calculate(self, query_tokens: list[str], disease: dict) -> Tuple[float, List[str], List[str]]:
        disease_symptoms = disease.get("symptoms", [])
        if not query_tokens or not disease_symptoms:
            return 0.0, [], disease_symptoms

        idf = getattr(self.db, "idf", {})
        total_score = 0.0
        matched_list, unmatched_list = [], []

        for ds in disease_symptoms:
            norm_ds = norm(ds)
            best_sim = max(
                (self._symptom_similarity(qt, norm_ds) for qt in query_tokens),
                default=0.0,
            )

            if best_sim >= _SIM_BROAD_CAT:
                total_score += best_sim * idf.get(norm_ds, 1.0)

            (matched_list if self._is_visual_match(norm_ds, query_tokens) else unmatched_list).append(ds)

        disease_total_weight = sum(idf.get(norm(ds), 1.0) for ds in disease_symptoms)
        score = total_score / disease_total_weight if disease_total_weight else 0.0

        has_critical_query = any(t in CRITICAL_SYMPTOMS for t in query_tokens)
        has_critical_match = any(norm(m) in CRITICAL_SYMPTOMS for m in matched_list)
        if has_critical_query and has_critical_match:
            score = min(1.0, score + _CRITICAL_BOOST)

        return round(min(score, 1.0), 4), matched_list, unmatched_list


class SyntacticSimilarity(SimilarityCalculator):
    STOPWORDS = {"je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "ai", "as", "a", "avons", "avez", "ont", "de", "la", "le", "les"}

    def calculate(self, query_tokens: list[str], disease: dict) -> Tuple[float, List[str], List[str]]:
        disease_symptoms = disease.get("symptoms", [])

        # Normalisation + filtre des stopwords
        norm_query_tokens_set = {norm(qt) for qt in query_tokens if norm(qt) not in self.STOPWORDS}

        # Construction du vecteur TF-IDF pour la requête
        q_vec: dict[str, float] = {}
        for key in norm_query_tokens_set:
            if key in self.db.idf:
                q_vec[key] = self.db.idf[key]  # TF=1 × IDF

        # Récupération du vecteur TF-IDF de la maladie
        d_vec = self.db.get_disease_vector(disease["id"])
        cosine_score = self._cosine(q_vec, d_vec)

        matched_list = []
        unmatched_list = []

        # Matching exact après normalisation
        for ds in disease_symptoms:
            norm_ds = norm(ds)
            if norm_ds in norm_query_tokens_set:
                matched_list.append(ds)
            else:
                unmatched_list.append(ds)

        coverage = len(matched_list) / len(disease_symptoms) if disease_symptoms else 0.0
        score = 0.7 * cosine_score + 0.3 * coverage

        return min(1.0, score), matched_list, unmatched_list
class HybridSimilarity(SimilarityCalculator):
    def __init__(self, db: MedicalDatabase, syntactic=None, semantic=None):
        super().__init__(db)
        self._syntactic = syntactic or SyntacticSimilarity(db)
        self._semantic = semantic or SemanticSimilarity(db)

    def calculate(self, query_tokens: list[str], disease: dict) -> Tuple[float, List[str], List[str]]:
        norm_query_tokens = [norm(t) for t in query_tokens]
        syn_score, syn_match, syn_unmatch = self._syntactic.calculate(query_tokens, disease)
        sem_score, sem_match, sem_unmatch = self._semantic.calculate(query_tokens, disease)

        alpha = 0.3 if any(norm(t) in CRITICAL_SYMPTOMS for t in norm_query_tokens) else 0.5
        final_score = alpha * syn_score + (1 - alpha) * sem_score

        # FIX : comparaison normalisée pour éviter le bug "symptôme présent
        # dans le match_set mais non coché" causé par les accents / casse.
        # On compare norm(ds) contre le set de formes normalisées.
        match_set = {norm(s) for s in syn_match} | {norm(s) for s in sem_match}

        hybrid_matched = []
        hybrid_unmatched = []
        for ds in disease.get("symptoms", []):
            if norm(ds) in match_set:   # ← FIX : norm(ds) au lieu de ds
                hybrid_matched.append(ds)
            else:
                hybrid_unmatched.append(ds)

        return round(min(final_score, 1.0), 4), hybrid_matched, hybrid_unmatched