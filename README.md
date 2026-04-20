# Dashboard IDC — Analyse des indices de dépense calorifique

Application Streamlit pour visualiser et analyser les IDC (Indices de Dépense Calorifique) des bâtiments genevois. Les données proviennent de la base SCANE_INDICE_MOYENNES_3_ANS du [SITG](https://ge.ch/sitg/).

## Prérequis

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets)
- Une instance Supabase (PostgreSQL) pour le cache des adresses, l'historique et les favoris

## Installation

```bash
git clone https://github.com/denisiglesiasgarcia/calcul_idc_dashboard.git
cd calcul_idc_dashboard
uv sync
```

## Configuration

Créer le fichier `.streamlit/secrets.toml` avec les identifiants de connexion à la base de données :

```toml
[supabase]
host     = "db.<project>.supabase.co"
port     = 5432
dbname   = "postgres"
user     = "postgres"
password = "..."
```

## Lancement

```bash
uv run streamlit run main.py
```

## Fonctionnalités

### Sélection des bâtiments

- Recherche par adresse (base locale synchronisée depuis le SITG)
- Sauvegarde de sélections sous forme de favoris
- Historique des consultations

### Visualisations

- Graphique en barres de l'IDC annuel par bâtiment, avec moyenne glissante sur 3 ans
- Carte géographique avec coloration par niveau d'IDC
- Tableaux détaillés : données brutes, agrégation par année, agents énergétiques, surface SRE

### Indicateurs clés (KPIs)

- IDC courant et moyenne 3 ans pondérés par la SRE
- Évolution entre la première et la dernière année disponible
- Détection des changements d'agent énergétique et de surface

### Export

- Téléchargement de chaque tableau en `.xlsx`

## Tests

```bash
uv run pytest
```

Les tests unitaires couvrent la validation de schéma, l'export Excel, la transformation de géométrie (LV95 → WGS84) et les appels à l'API SITG (avec mocks HTTP).

## Mise à jour des adresses

La liste des adresses est stockée localement dans Supabase. Pour la synchroniser avec le SITG, utiliser le bouton **Mettre à jour les adresses** dans la barre latérale de l'application.
