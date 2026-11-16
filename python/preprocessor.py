import re
from .exceptions import PreprocessingError
from .database import norm, MedicalDatabase

# Stop words consolidés
_RAW_STOP_WORDS = {
    "je", "tu", "il", "nous", "vous", "ils", "elles", "on", "le", "la", "les",
    "un", "une", "des", "de", "du", "ce", "cette", "ces", "mon", "ma", "mes",
    "son", "sa", "ses", "à", "au", "aux", "en", "et", "est", "ou", "mais",
    "donc", "car", "ni", "comme", "très", "aussi", "avec", "dans", "sur", "par",
    "pour", "sans", "vers", "entre", "chez", "suis", "ai", "a", "avoir", "être",
    "sont", "ont", "été", "fait", "peut", "qui", "que", "ne", "pas", "plus",
    "tout", "tous", "toute", "toutes", "autre", "autres", "même", "bien", "mal",
    "encore", "depuis", "j", "m", "t", "s", "l", "n", "c", "d", "qu", "j'ai", "elle",
    "avoir", "souffre", "ressens"
}
STOP_WORDS: frozenset[str] = frozenset(norm(w) for w in _RAW_STOP_WORDS)

# Lemmatisation rapatriée ici (sa vraie place)
LEMMA_MAP = {
    "tousse": "toux", "toussant": "toux", "tousser": "toux",
    "fievreux": "fievre", "fievreuse": "fievre", "essoufle": "essoufflement",
    "essouflee": "essoufflement", "respire": "difficultes respiratoires",
    "respiration": "difficultes respiratoires", "douloureux": "douleur",
    "douloureuse": "douleur", "fatiguee": "fatigue", "nausee": "nausees",
    "vomis": "vomissements", "vomir": "vomissements", "vomissement": "vomissements",
}

QUALIFIERS = {"legere", "moderee", "persistante", "intense", "forte"}


class TextPreprocessor:
    """Transforme une requête en français en entités de symptômes."""

    _PUNCT_PATTERN = re.compile(r"[;,.!?(){}\[\]:/\\-]+")
    _SPACES_PATTERN = re.compile(r"\s+")
    _APOSTROPHE_PATTERN = re.compile(r"[''`]+")

    def __init__(self, db: MedicalDatabase):
        self.db = db
        # On trie le vocabulaire du plus long au plus court pour matcher
        # "maux de tete" avant "maux" ou "tete".
        self.sorted_vocab = sorted(list(self.db.vocabulary), key=len, reverse=True)

    def tokenize(self, text: str,strict_syntax: bool = False) -> list[str]:
        """Extrait intelligemment les symptômes (multi-mots inclus)."""
        if not text or not isinstance(text, str):
            raise PreprocessingError("Le texte à tokeniser est vide ou invalide")

        text = text.lower()
        text = self._APOSTROPHE_PATTERN.sub(" ", text)
        text = self._PUNCT_PATTERN.sub(" ", text)
        text = self._SPACES_PATTERN.sub(" ", text).strip()

        normalized_text = norm(text)

        # 1. Extraction d'entités multi-mots (N-Gram Matching)
        extracted_entities = []
        for vocab_term in self.sorted_vocab:
            # Si le terme du vocabulaire est dans le texte
            if re.search(r'\b' + re.escape(vocab_term) + r'\b', normalized_text):
                extracted_entities.append(vocab_term)
                # On retire le terme du texte pour ne pas le re-processer
                normalized_text = re.sub(r'\b' + re.escape(vocab_term) + r'\b', ' ', normalized_text)

        # 2. Traitement des mots restants (Stop words, lemmes, qualificatifs)
        remaining_words = normalized_text.split()
        # Traitement des mots restants
        for w in remaining_words:
            if w in STOP_WORDS or w in QUALIFIERS or len(w) <= 1:
                continue

            if strict_syntax:
                # STRICT : on ne fait ni lemme ni synonyme
                canonical = w
            else:
                # NORMAL : appliquer lemmatisation + synonymes
                lemmatized = LEMMA_MAP.get(w, w)
                canonical = self.db.norm_synonym_to_canonical.get(lemmatized, lemmatized)

            extracted_entities.append(canonical)
        # Dédoublonner en gardant l'ordre
        result = list(dict.fromkeys(extracted_entities))

        if not result:
            raise PreprocessingError("Aucun symptôme identifiable dans la requête")

        return result