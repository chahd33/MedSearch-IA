from .exceptions import SearchError, PreprocessingError
from .preprocessor import TextPreprocessor
from .similarity import SyntacticSimilarity, SemanticSimilarity, HybridSimilarity


class SearchEngine:
    def __init__(self, db):
        if not db:
            raise SearchError("Base de données invalide ou vide")

        self.db = db
        # Le Preprocessor a maintenant besoin de la DB pour l'Entity Extraction
        self.preprocessor = TextPreprocessor(db)

        _syntactic = SyntacticSimilarity(db)
        _semantic = SemanticSimilarity(db)

        self.calculators = {
            "syntactic": _syntactic,
            "semantic": _semantic,
            "hybrid": HybridSimilarity(db, syntactic=_syntactic, semantic=_semantic),
        }
        self.current_mode = "hybrid"

    def set_mode(self, mode: str) -> None:
        if mode not in self.calculators:
            raise SearchError(f"Mode inconnu : {mode}")
        self.current_mode = mode

    def search(self, raw_query: str) -> dict:
        try:
            # 1 — NLP Pipeline unifiée (Renvoie des entités propres, ex: ["maux de tete", "fievre"])
            tokens = self.preprocessor.tokenize(raw_query)

            calculator = self.calculators[self.current_mode]
            results = []

            # 2 — Calcul des scores ET récupération des matchs en 1 seule passe O(N) !
            for disease in self.db.diseases:
                score, matched, unmatched = calculator.calculate(tokens, disease)

                if score <= 0.15:
                    continue

                if len(matched) == 1 and len(disease.get('symptoms', [])) > 3:
                    score *= 0.7  # Pénalité si 1 seul symptôme sur une maladie complexe

                results.append({
                    "disease": disease.get("name", ""),
                    "diseaseId": disease.get("id", ""),
                    "score": round(score, 4),
                    "scorePercent": round(score * 100),
                    "matchedSymptoms": matched,
                    "unmatchedSymptoms": unmatched,
                    "matchRatio": f"{len(matched)}/{len(disease.get('symptoms', []))}",
                })

            # 3 — Tri et limitation top 5
            results.sort(key=lambda r: r["score"], reverse=True)
            results = results[:5]

            return {
                "query": raw_query,
                "extracted_entities": tokens,  # Plus parlant que "tokens" pour le debug Frontend
                "mode": self.current_mode,
                "count": len(results),
                "results": results,
            }

        except PreprocessingError as e:
            raise SearchError(e.message) from e
        except Exception as e:
            raise SearchError(f"Erreur inattendue : {e}") from e