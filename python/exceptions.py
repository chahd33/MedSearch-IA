"""
MedSearch IA — Hiérarchie d'exceptions personnalisées.

Chaque couche de l'application lève sa propre exception typée,
ce qui permet un diagnostic précis des erreurs remontées à l'API.
"""


class MedSearchError(Exception):
    """Exception de base pour tout le projet MedSearch."""

    def __init__(self, message: str, source: str = ""):
        super().__init__(message)
        self.message = message
        self.source = source

    def __str__(self):
        return f"[{self.source}] {self.message}"


class DatabaseError(MedSearchError):
    """Erreur liée au chargement ou à l'interrogation de la base locale."""

    def __init__(self, msg: str):
        super().__init__(msg, source="Database")


class PreprocessingError(MedSearchError):
    """Erreur survenue lors du prétraitement / tokenisation."""

    def __init__(self, msg: str):
        super().__init__(msg, source="Preprocessor")


class SimilarityError(MedSearchError):
    """Erreur dans le calcul de similarité."""

    def __init__(self, msg: str):
        super().__init__(msg, source="Similarity")


class SearchError(MedSearchError):
    """Erreur dans le moteur de recherche."""

    def __init__(self, msg: str):
        super().__init__(msg, source="SearchEngine")


class WebSearchError(MedSearchError):
    """Erreur lors de la construction des liens web."""

    def __init__(self, msg: str):
        super().__init__(msg, source="WebSearcher")