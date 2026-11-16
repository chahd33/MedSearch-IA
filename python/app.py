"""
MedSearch IA — Serveur Flask exposant l'API REST.

Endpoints
---------
GET /api/search?query=...&mode=...
    Recherche de pathologies à partir de symptômes.

GET /api/suggestions?input=...
    Suggestions de symptômes en temps réel.

GET /api/stats
    Statistiques de la base de données.

GET /api/modes
    Liste des modes de similarité disponibles.

GET /api/web-links?query=...
    Liens de recherche vers les sources médicales fiables.

GET /
    Sert le fichier index.html (frontend via render_template).

CORRECTIONS v2 :
  - Route "/" dupliquée supprimée : home() + serve_index() définissaient
    tous les deux @app.route("/") → AssertionError au démarrage Flask.
    serve_index() (send_from_directory) est supprimée ; home() avec
    render_template est conservée.
  - CORS(app) déplacé immédiatement après app = Flask(...) pour qu'il
    s'applique à toutes les routes sans exception.
  - Routes serve_css() et serve_js() supprimées : Flask sert déjà
    automatiquement /static/** via static_folder="../static".
  - BASE_DIR supprimé (devenu inutile).
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from .exceptions import MedSearchError
from .database import MedicalDatabase
from .search_engine import SearchEngine
from .web_searcher import WebSearcher


# ------------------------------------------------------------------
# Initialisation de l'application
# ------------------------------------------------------------------

app = Flask(
    __name__,
    static_folder="../static",
    static_url_path="",        # ← Flask servira /css/... au lieu de /static/css/...
    template_folder="../templates",
)

# FIX : CORS appliqué immédiatement après la création de l'app,
# avant toute déclaration de route, pour couvrir toutes les routes
# sans exception (order-sensitive dans Flask).
CORS(app)

# Instanciation unique des composants métier
db = MedicalDatabase()
engine = SearchEngine(db)


# ------------------------------------------------------------------
# Routes frontend
# ------------------------------------------------------------------

@app.route("/")
def home():
    """Sert la page principale.
    FIX : route unique — serve_index() supprimée (doublon qui causait
    AssertionError au démarrage).
    """
    return render_template("index.html")


# ------------------------------------------------------------------
# Routes API
# ------------------------------------------------------------------

@app.route("/api/search")
def api_search():
    """Recherche de pathologies."""
    query = request.args.get("query", "").strip()
    mode  = request.args.get("mode", "hybrid").strip()

    if not query:
        return jsonify({"error": True, "message": "Paramètre 'query' requis"}), 400

    try:
        engine.set_mode(mode)
        result = engine.search(query)
        return jsonify({"error": False, "data": result})

    except MedSearchError as e:
        return jsonify({
            "error":   True,
            "message": e.message,
            "source":  e.source,
        }), 422

    except Exception as e:
        return jsonify({"error": True, "message": f"Erreur interne : {e}"}), 500


@app.route("/api/suggestions")
def api_suggestions():
    """Suggestions de symptômes en temps réel."""
    input_text = request.args.get("input", "").strip()

    if not input_text or len(input_text) < 2:
        return jsonify({"error": False, "data": []})

    try:
        suggestions = db.find_similar_symptoms(input_text)
        return jsonify({"error": False, "data": suggestions})
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """Statistiques de la base."""
    return jsonify({"error": False, "data": db.stats})


@app.route("/api/modes")
def api_modes():
    """Liste des modes de similarité."""
    modes = [
        {"id": "syntactic", "label": "Syntaxique (TF-IDF)"},
        {"id": "semantic",  "label": "Sémantique (Ontologie)"},
        {"id": "hybrid",    "label": "Hybride (TF-IDF + Ontologie)"},
    ]
    return jsonify({"error": False, "data": modes})


@app.route("/api/web-links")
def api_web_links():
    """Liens de recherche web."""
    query = request.args.get("query", "").strip()

    if not query:
        return jsonify({"error": True, "message": "Paramètre 'query' requis"}), 400

    try:
        links = WebSearcher.generate_links(query)
        return jsonify({"error": False, "data": links})
    except MedSearchError as e:
        return jsonify({"error": True, "message": e.message}), 422


# ------------------------------------------------------------------
# Point d'entrée
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  MedSearch IA — Serveur démarré sur http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host="127.0.0.1", port=5000, debug=True)