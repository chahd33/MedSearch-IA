"""
MedSearch IA — Données médicales de référence.

Contient :
  - La base locale de 35 pathologies avec leurs symptômes
  - Un dictionnaire de synonymes médicaux (~40 groupes)
  - Une catégorisation par système physiologique (11 catégories)
  - La liste des sources médicales fiables pour la recherche web

Toutes les données sont regroupées ici pour faciliter la maintenance
et l'extension de la base.

CORRECTIONS v2 :
  - "toux persistante" retiré des synonymes (c'est un symptôme propre de Bronchite,
    l'avoir aussi comme synonyme de "toux" causait un double-comptage dans
    get_query_vector()).
  - Catégorie "sensoriel" supprimée : ses 3 symptômes ont été redistribués dans
    "neurologique" (perte de goût, perte d'odorat) et "ORL" (sensibilité au bruit).
    La catégorie était trop pauvre pour contribuer au score sémantique.
  - Doublon "insomnie" retiré de "psychiatrique" (déjà dans troubles_du_sommeil).
"""


class MedicalData:
    """Classe statique centralisant toutes les données médicales."""

    # ------------------------------------------------------------------
    # BASE LOCALE DE PATHOLOGIES
    # ------------------------------------------------------------------
    @staticmethod
    def get_diseases() -> list[dict]:
        """Retourne la liste des maladies indexées."""
        return [
            {
                "id": 1,
                "name": "Grippe",
                "symptoms": [
                    "fièvre", "toux", "fatigue", "courbatures",
                    "maux de tête", "congestion nasale", "frissons",
                ],
            },
            {
                "id": 2,
                "name": "COVID-19",
                "symptoms": [
                    "fièvre", "toux", "fatigue", "perte de goût",
                    "perte d'odorat", "difficultés respiratoires", "maux de tête",
                ],
            },
            {
                "id": 3,
                "name": "Migraine",
                "symptoms": [
                    "maux de tête intenses", "nausées",
                    "sensibilité à la lumière", "sensibilité au bruit",
                    "vision trouble",
                ],
            },
            {
                "id": 4,
                "name": "Appendicite aiguë",
                "symptoms": [
                    "douleur abdominale", "nausées", "vomissements",
                    "fièvre", "perte d'appétit",
                ],
            },
            {
                "id": 5,
                "name": "Pneumonie",
                "symptoms": [
                    "toux", "fièvre", "difficultés respiratoires",
                    "douleurs thoraciques", "fatigue", "frissons",
                ],
            },
            {
                "id": 6,
                "name": "Diabète de type 2",
                "symptoms": [
                    "soif excessive", "mictions fréquentes", "fatigue",
                    "vision trouble", "perte de poids",
                ],
            },
            {
                "id": 7,
                "name": "Hypertension artérielle",
                "symptoms": [
                    "maux de tête", "vertiges", "saignements de nez",
                    "essoufflement", "bourdonnements d'oreilles",
                ],
            },
            {
                "id": 8,
                "name": "Asthme",
                "symptoms": [
                    "essoufflement", "sifflements respiratoires", "toux",
                    "oppression thoracique", "difficultés respiratoires",
                ],
            },
            {
                "id": 9,
                "name": "Allergie saisonnière",
                "symptoms": [
                    "éternuements", "démangeaisons", "écoulement nasal",
                    "yeux larmoyants", "congestion nasale",
                ],
            },
            {
                "id": 10,
                "name": "Gastro-entérite",
                "symptoms": [
                    "nausées", "vomissements", "diarrhée",
                    "douleurs abdominales", "fièvre", "déshydratation",
                ],
            },
            {
                "id": 11,
                "name": "Bronchite aiguë",
                "symptoms": [
                    "toux persistante", "expectorations", "fatigue",
                    "fièvre légère", "gêne respiratoire",
                ],
            },
            {
                "id": 12,
                "name": "Sinusite",
                "symptoms": [
                    "congestion nasale", "douleurs faciales", "maux de tête",
                    "écoulement nasal", "fièvre légère",
                ],
            },
            {
                "id": 13,
                "name": "Angine à streptocoque",
                "symptoms": [
                    "mal de gorge", "difficulté à avaler", "fièvre",
                    "amygdales rouges", "ganglions enflés",
                ],
            },
            {
                "id": 14,
                "name": "Anémie ferriprive",
                "symptoms": [
                    "fatigue", "pâleur", "essoufflement", "vertiges",
                    "faiblesse", "maux de tête",
                ],
            },
            {
                "id": 15,
                "name": "Dépression majeure",
                "symptoms": [
                    "tristesse persistante", "fatigue", "troubles du sommeil",
                    "perte d'intérêt", "difficultés de concentration",
                    "perte d'appétit",
                ],
            },
            {
                "id": 16,
                "name": "Trouble anxieux",
                "symptoms": [
                    "inquiétude excessive", "palpitations", "tremblements",
                    "sueurs", "insomnie", "agitation",
                ],
            },
            {
                "id": 17,
                "name": "Polyarthrite rhumatoïde",
                "symptoms": [
                    "douleurs articulaires", "raideur matinale",
                    "gonflement articulaire", "fatigue",
                    "limitation des mouvements",
                ],
            },
            {
                "id": 18,
                "name": "Eczéma atopique",
                "symptoms": [
                    "démangeaisons", "rougeurs cutanées", "sécheresse de la peau",
                    "lésions cutanées", "desquamation",
                ],
            },
            {
                "id": 19,
                "name": "Rhinite allergique",
                "symptoms": [
                    "éternuements", "congestion nasale", "écoulement nasal",
                    "démangeaisons nasales", "démangeaisons oculaires",
                ],
            },
            {
                "id": 20,
                "name": "Otite moyenne",
                "symptoms": [
                    "douleur auriculaire", "fièvre", "difficulté à entendre",
                    "écoulement auriculaire", "irritabilité",
                ],
            },
            {
                "id": 21,
                "name": "Conjonctivite",
                "symptoms": [
                    "rougeur oculaire", "démangeaisons oculaires",
                    "sécrétions oculaires", "gonflement des paupières",
                    "larmoiement",
                ],
            },
            {
                "id": 22,
                "name": "Insuffisance rénale",
                "symptoms": [
                    "fatigue", "œdèmes", "mictions réduites", "nausées",
                    "essoufflement", "démangeaisons",
                ],
            },
            {
                "id": 23,
                "name": "Hypothyroïdie",
                "symptoms": [
                    "fatigue", "prise de poids", "frilosité",
                    "sécheresse cutanée", "constipation", "perte de cheveux",
                ],
            },
            {
                "id": 24,
                "name": "Hyperthyroïdie",
                "symptoms": [
                    "perte de poids", "palpitations", "nervosité",
                    "transpiration excessive", "tremblements", "insomnie",
                ],
            },
            {
                "id": 25,
                "name": "Maladie de Parkinson",
                "symptoms": [
                    "tremblements au repos", "lenteur des mouvements",
                    "rigidité musculaire", "instabilité posturale",
                    "écriture petite",
                ],
            },
            {
                "id": 26,
                "name": "Sclérose en plaques",
                "symptoms": [
                    "fatigue", "troubles de la vision", "engourdissements",
                    "faiblesse musculaire", "troubles de l'équilibre",
                ],
            },
            {
                "id": 27,
                "name": "Maladie d'Alzheimer",
                "symptoms": [
                    "perte de mémoire", "confusion", "difficultés de langage",
                    "désorientation", "troubles du jugement",
                ],
            },
            {
                "id": 28,
                "name": "Goutte",
                "symptoms": [
                    "douleur articulaire intense", "rougeur articulaire",
                    "gonflement", "chaleur locale", "immobilité articulaire",
                ],
            },
            {
                "id": 29,
                "name": "Hernie discale lombaire",
                "symptoms": [
                    "douleur dorsale", "sciatique",
                    "engourdissements des jambes", "faiblesse musculaire",
                    "douleur en position assise",
                ],
            },
            {
                "id": 30,
                "name": "Phlébite profonde",
                "symptoms": [
                    "douleur à la jambe", "gonflement du mollet", "rougeur",
                    "chaleur locale", "dilatation veineuse",
                ],
            },
            {
                "id": 31,
                "name": "Intoxication alimentaire",
                "symptoms": [
                    "nausées", "vomissements", "diarrhée",
                    "crampes abdominales", "fièvre", "frissons",
                ],
            },
            {
                "id": 32,
                "name": "Mononucléose infectieuse",
                "symptoms": [
                    "fatigue intense", "fièvre", "mal de gorge",
                    "gonflement des ganglions", "splénomégalie",
                ],
            },
            {
                "id": 33,
                "name": "Varicelle",
                "symptoms": [
                    "éruption cutanée", "fièvre", "démangeaisons intenses",
                    "fatigue", "perte d'appétit",
                ],
            },
            {
                "id": 34,
                "name": "Méningite",
                "symptoms": [
                    "maux de tête intenses", "fièvre élevée",
                    "raideur de la nuque", "photophobie", "nausées",
                    "vomissements",
                ],
            },
            {
                "id": 35,
                "name": "Zona",
                "symptoms": [
                    "douleur localisée", "éruption vésiculeuse", "brûlures",
                    "picotements", "fièvre légère", "fatigue",
                ],
            },
        ]

    # ------------------------------------------------------------------
    # DICTIONNAIRE DE SYNONYMES MÉDICAUX
    # ------------------------------------------------------------------
    @staticmethod
    def get_synonyms() -> dict[str, list[str]]:
        """
        Retourne la map symptôme-clé → liste de synonymes.

        Règle : un terme qui est déjà un symptôme propre dans get_diseases()
        ne doit PAS apparaître ici comme synonyme d'un autre terme, pour éviter
        le double-comptage dans get_query_vector().
        Ex : "toux persistante" est le symptôme propre de Bronchite aiguë →
             retiré des synonymes de "toux".
        """
        return {
            "maux de tête": ["céphalées", "headache", "mal de crâne"],
            "fièvre": ["température élevée", "hyperthermie", "fébricule", "avoir chaud"],
            # FIX : "toux persistante" retiré — c'est un symptôme propre (Bronchite)
            "toux": ["toux sèche", "toux grasse"],
            "fatigue": [
                "asthénie", "épuisement", "faiblesse générale",
                "manque d'énergie", "fatigue intense",
            ],
            "nausées": ["envie de vomir", "malaise gastrique", "nausée"],
            "vomissements": ["rejets", "régurgitations", "vomissement"],
            "douleur": ["douleurs", "algie", "sensation douloureuse"],
            "éruption cutanée": [
                "rash", "lésions cutanées", "boutons",
                "éruption", "plaques rouges",
            ],
            "essoufflement": [
                "dyspnée", "difficulté à respirer",
                "essoufflé", "manque de souffle",
            ],
            "vertiges": ["étourdissements", "tournis", "vertige", "sens de vertige"],
            "démangeaisons": [
                "prurit", "grattage", "démangeaison",
                "démangeaisons intenses",
            ],
            "perte de poids": ["amaigrissement", "cachexie", "maigrissement"],
            "palpitations": ["battements rapides", "tachycardie", "cœur qui bat vite"],
            "perte d'appétit": ["anorexie", "absence de faim", "dégoût alimentaire"],
            "douleurs abdominales": [
                "mal de ventre", "crampes abdominales",
                "douleur au ventre", "douleur à l'estomac",
            ],
            "congestion nasale": [
                "nez bouché", "obstruction nasale",
                "congestion", "nez congestionné",
            ],
            "écoulement nasal": ["rhinorrhée", "nez qui coule", "écoulement"],
            "difficultés respiratoires": [
                "dyspnée", "respiration difficile",
                "essoufflement sévère",
            ],
            "douleurs thoraciques": [
                "douleur à la poitrine",
                "douleur dans la poitrine",
                "oppression thoracique",
            ],
            "douleur auriculaire": [
                "mal d'oreille", "otalgie", "douleur à l'oreille",
            ],
            "rougeur oculaire": [
                "œil rouge", "hyperhémie conjonctivale", "rougeur des yeux",
            ],
            "engourdissements": [
                "fourmillements", "paresthésies",
                "picotements", "sensation de fourmis",
            ],
            "troubles du sommeil": [
                "insomnie", "difficulté à dormir",
                "sommeil perturbé", "insomnies",
            ],
            "perte de mémoire": [
                "troubles mnésiques", "oubli", "amnésie",
                "troubles de la mémoire",
            ],
            "gonflement": [
                "œdème", "enflure", "gonflement articulaire", "swelling",
            ],
            "transpiration excessive": [
                "hyperhidrose", "sueurs abondantes", "sueurs nocturnes",
            ],
            "fièvre légère": ["subfébrilité", "légère température", "fièvre modérée"],
            "maux de tête intenses": [
                "céphalées sévères", "migraine",
                "douleur crânienne intense",
            ],
            "sensibilité à la lumière": ["photophobie", "intolérance à la lumière"],
            "yeux larmoyants": ["larmoiement", "épiphora", "yeux qui pleurent"],
            "expectorations": ["crachats", "mucus", "glaires"],
            "gêne respiratoire": [
                "inconfort respiratoire", "difficulté respiratoire légère",
            ],
            "sifflements respiratoires": [
                "sifflements", "wheezing", "respiration sifflante",
            ],
            "troubles de la vision": [
                "vision floue", "trouble visuel", "baisse de vision",
            ],
            "douleurs articulaires": [
                "arthralgies", "douleur aux articulations", "algies articulaires",
            ],
            "sciatique": [
                "douleur sciatique", "névralgie sciatique", "douleur dans la jambe",
            ],
        }

    # ------------------------------------------------------------------
    # CATÉGORISATION PAR SYSTÈME PHYSIOLOGIQUE
    # ------------------------------------------------------------------
    @staticmethod
    def get_categories() -> dict[str, list[str]]:
        """
        Retourne la map catégorie → liste de symptômes.

        CORRECTIONS v2 :
          - Catégorie "sensoriel" supprimée (trop pauvre, 3 symptômes quasi-exclusifs
            à COVID-19/migraine → score sémantique nul pour le reste).
          - "perte de goût" et "perte d'odorat" → "neurologique"
            (chémosensorialité, origine nerveuse centrale).
          - "sensibilité au bruit" → "ORL"
          - "insomnie" dédupliqué dans "psychiatrique"
            (déjà couvert par "troubles du sommeil").
        """
        return {
            "respiratoire": [
                "toux", "toux persistante", "essoufflement",
                "sifflements respiratoires", "congestion nasale",
                "écoulement nasal", "difficultés respiratoires",
                "expectorations", "gêne respiratoire",
                "oppression thoracique", "dyspnée",
            ],
            "digestif": [
                "nausées", "vomissements", "diarrhée",
                "douleurs abdominales", "douleur abdominale",
                "perte d'appétit", "constipation",
                "crampes abdominales", "mal de gorge",
                "difficulté à avaler", "déshydratation",
            ],
            "neurologique": [
                "maux de tête", "maux de tête intenses", "vertiges",
                "engourdissements", "confusion", "désorientation",
                "perte de mémoire", "tremblements", "lenteur des mouvements",
                "troubles de l'équilibre", "écriture petite",
                "instabilité posturale", "troubles du jugement",
                # FIX : anciennement dans "sensoriel"
                "perte de goût", "perte d'odorat",
            ],
            "cutané": [
                "démangeaisons", "rougeurs cutanées", "sécheresse de la peau",
                "lésions cutanées", "desquamation", "éruption cutanée",
                "éruption vésiculeuse", "brûlures", "picotements",
                "rougeur", "chaleur locale", "perte de cheveux",
                "sécheresse cutanée",
            ],
            "articulaire": [
                "douleurs articulaires", "raideur matinale",
                "gonflement articulaire", "limitation des mouvements",
                "douleur articulaire intense", "immobilité articulaire",
                "rigidité musculaire", "douleur dorsale", "sciatique",
                "douleur à la jambe",
            ],
            "général": [
                "fièvre", "fièvre légère", "fièvre élevée", "fatigue",
                "frissons", "perte de poids", "prise de poids",
                "transpiration excessive", "fatigue intense", "frilosité",
                "pâleur", "faiblesse", "faiblesse musculaire",
                "splénomégalie", "courbatures",
            ],
            "oculaire": [
                "vision trouble", "rougeur oculaire",
                "sensibilité à la lumière", "sécrétions oculaires",
                "gonflement des paupières", "yeux larmoyants",
                "troubles de la vision", "larmoiement",
                "démangeaisons oculaires", "photophobie",
            ],
            "ORL": [
                "mal de gorge", "difficulté à avaler", "douleur auriculaire",
                "écoulement auriculaire", "douleurs faciales",
                "démangeaisons nasales", "saignements de nez",
                "bourdonnements d'oreilles", "amygdales rouges",
                "ganglions enflés", "difficulté à entendre", "irritabilité",
                "éternuements",
                # FIX : anciennement dans "sensoriel"
                "sensibilité au bruit",
            ],
            "urinaire": [
                "soif excessive", "mictions fréquentes", "mictions réduites",
                "œdèmes",
            ],
            "psychiatrique": [
                "tristesse persistante", "inquiétude excessive", "agitation",
                "nervosité", "perte d'intérêt", "difficultés de concentration",
                # FIX : "insomnie" retiré (déjà dans "troubles du sommeil" ci-dessous)
                "troubles du sommeil",
            ],
            "cardiovasculaire": [
                "palpitations", "douleurs thoraciques", "dilatation veineuse",
            ],
        }

    # ------------------------------------------------------------------
    # SOURCES MÉDICALES FIABLES POUR LA RECHERCHE WEB
    # ------------------------------------------------------------------
    @staticmethod
    def get_web_sources() -> list[dict]:
        """Retourne la liste des sources web médicales de confiance."""
        return [
            {
                "name": "PubMed",
                "url": "https://pubmed.ncbi.nlm.nih.gov/?term=",
                "icon": "fa-solid fa-book-medical",
                "color": "#E05D44",
                "desc": "Articles scientifiques revisés par les pairs",
            },
            {
                "name": "OMS / WHO",
                "url": "https://www.who.int/search?q=",
                "icon": "fa-solid fa-earth-americas",
                "color": "#009CDC",
                "desc": "Recommandations mondiales de santé",
            },
            {
                "name": "Mayo Clinic",
                "url": "https://www.mayoclinic.org/search/search-results?q=",
                "icon": "fa-solid fa-hospital",
                "color": "#0072CE",
                "desc": "Information clinique de référence",
            },
            {
                "name": "MSD Manuel",
                "url": "https://www.msdmanuals.com/fr/rechercher?q=",
                "icon": "fa-solid fa-stethoscope",
                "color": "#8B1A4A",
                "desc": "Manuel médical complet en français",
            },
            {
                "name": "Vidal",
                "url": "https://www.vidal.fr/recherche.html?q=",
                "icon": "fa-solid fa-pills",
                "color": "#E4003A",
                "desc": "Base de données médicaments et pathologies",
            },
            {
                "name": "Ameli.fr",
                "url": "https://www.ameli.fr/assure/sante/recherche?q=",
                "icon": "fa-solid fa-shield-heart",
                "color": "#1A6FB5",
                "desc": "Assurance Maladie — informations santé officielles",
            },
        ]