"""
MedSearch IA — Génération de liens vers des sources médicales fiables.

Prend une requête et retourne les URL pré-construites vers
6 sites médicaux de confiance.
"""

from urllib.parse import quote
from .exceptions import WebSearchError
from .data import MedicalData


class WebSearcher:
    """Génère des liens de recherche web pour des sources médicales."""

    @staticmethod
    def generate_links(query: str) -> list[dict]:
        """
        Construit les liens de recherche pour chaque source fiable.

        Paramètres
        ----------
        query : str
            Requête de l'utilisateur.

        Retourne
        -------
        list[dict]
            Liste de {name, url, icon, color, desc}.

        Lève
        -----
        WebSearchError
            Si la requête est vide.
        """
        if not query or not query.strip():
            raise WebSearchError("Requête vide pour la recherche web")

        encoded = quote(query.strip())
        sources = MedicalData.get_web_sources()

        return [
            {
                "name": src["name"],
                "url": src["url"] + encoded,
                "icon": src["icon"],
                "color": src["color"],
                "desc": src["desc"],
            }
            for src in sources
        ]