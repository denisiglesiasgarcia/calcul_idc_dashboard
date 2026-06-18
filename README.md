# Dashboard analyse IDC

[calculidc.streamlit.app/](https://calculidc.streamlit.app)

Application Streamlit pour visualiser et analyser les IDC (Indices de Dépense Chaleur). Les données proviennent de [SCANE_INDICE_MOYENNES_3_ANS](https://sitg.ge.ch/donnees/scane-indice-moyennes-3-ans).

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

## Lancement

```bash
uv run streamlit run main.py
```

## Source des données
- [SCANE_INDICE_MOYENNES_3_ANS](https://sitg.ge.ch/donnees/scane-indice-moyennes-3-ans) : données IDC
- [SIT_AUTOR_DOSSIER](https://sitg.ge.ch/donnees/sit-autor-dossier) : autorisations de construire avec un point qui géolocalise le dossier
- [CAD_BATIMENT_HORSOL](https://sitg.ge.ch/donnees/cad-batiment-horsol) : cadastre des bâtiments hors-sol avec le polygone d'emprise au sol du bâtiment

## Fonctionnalités

### Sélection des bâtiments

- Recherche par adresse (base de données locale sqlite mise à jour depuis SITG)
- Analyse de plusieurs bâtiments au même temps
- Sauvegarde favoris
- Historique

### Visualisations

- Graphique en barres de l'évolution de l'IDC par année
- Plan de situation OpenStreetMap (infobulle enrichie des caractéristiques du bâtiment : construction, niveaux, hauteur, emprise, destination)
- Données tabulaires
  - Toutes les données
  - IDC pondéré par année (cas plusieurs bâtiments) avec variations
  - Agents énergétiques par année et par bâtiment (en jaune/gras si changement)
  - Surface de référence énergétique par année et bâtiment (en jaune/gras si changement)
  - Caractéristiques des bâtiments (CAD_BATIMENT_HORSOL) : époque/année de construction, transformation, niveaux hors-sol/sous-sol, hauteur, emprise au sol, destination
  - Autorisations de construire (jointure spatiale entre le point du dossier et le polygone associé à l'EGID)

### Indicateurs clés (KPIs)

- Dernier IDC disponible et moyenne 3 ans pondérés par la SRE
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

La liste des adresses est stockée localement dans Sqlite et mise à jour automatiquement.
