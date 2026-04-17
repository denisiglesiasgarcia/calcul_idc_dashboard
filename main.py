# /main.py

from datetime import datetime
import polars as pl
import streamlit as st

from sections.helpers.db import (
    init_history_table,
    save_history_entry,
    load_history,
    delete_history_entry,
    refresh_adresses_db,
    init_favorites_table,
    save_favorite,
    load_favorites,
    delete_favorite,
    get_all_addresses,
)
from sections.helpers.idc_api import fetch_idc_data
from sections.helpers.idc_geo import convert_geometry_for_streamlit, show_map
from sections.helpers.idc_charts import create_barplot
from sections.helpers.idc_tables import show_kpis, show_dataframe

st.set_page_config(
    layout="wide",
    page_title="Dashboard analyse IDC",
    page_icon="📈",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.streamlit.io/community",
        "Report a bug": "https://github.com/denisiglesiasgarcia/calcul_idc_dashboard/issues",
        "About": "# Dashboard analyse IDC",
    },
)

# ---------------------------------------------------------------------------------------
FIELDS = "*"
URL_INDICE_MOYENNES_3_ANS = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/"
    "SCANE_INDICE_MOYENNES_3_ANS/FeatureServer/0/query"
)

CURRENT_YEAR = datetime.now().year

# Init DB au démarrage, session_state uniquement pour le reload sidebar
init_history_table()
init_favorites_table()


if "address_multiselect" not in st.session_state:
    st.session_state["address_multiselect"] = []

# ---------------------------------------------------------------------------------------
# Sidebar — analysis parameters
# ---------------------------------------------------------------------------------------
with st.sidebar:
    st.header("Paramètres d'analyse")

    seuil = st.number_input(
        label="Seuil IDC de référence [MJ/m²]",
        min_value=0,
        max_value=2000,
        value=0,
        step=10,
        help=("Valeur limite à Genève : 450 MJ/m²."),
    )

    year_range = st.slider(
        label="Période d'analyse",
        min_value=2011,
        max_value=CURRENT_YEAR,
        value=(2011, CURRENT_YEAR),
        step=1,
    )

    st.divider()

    st.subheader("Base de données locale")
    if st.button("Mettre à jour les adresses", use_container_width=True):
        status_text = st.empty()
        progress_bar = st.progress(0.0)
        try:
            n = refresh_adresses_db(
                URL_INDICE_MOYENNES_3_ANS,
                progress_bar=progress_bar,
                status_text=status_text,
            )
            # Clear the single address cache so the multiselect reloads
            get_all_addresses.clear()
            progress_bar.empty()
            status_text.empty()
            st.success(f"{n:,} adresses chargées et enregistrées.")
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Erreur lors de la mise à jour : {e}")
    st.caption(
        "Les données proviennent de la base SCANE_INDICE_MOYENNES_3_ANS "
        "du SITG (Genève)."
    )

    st.divider()
    st.subheader("Favoris")

    favorites = load_favorites()

    if not favorites:
        st.caption("Aucun favori enregistré.")
    else:
        fav_names = [f["name"] for f in favorites]
        selected_fav_name = st.selectbox(
            "Charger un favori",
            options=["—"] + fav_names,
            key="fav_selectbox",
            label_visibility="collapsed",
        )

        if selected_fav_name != "—":
            fav = next(f for f in favorites if f["name"] == selected_fav_name)
            col_load, col_del = st.columns([3, 1])
            with col_load:
                if st.button("Charger", key="btn_load_fav", use_container_width=True):
                    st.session_state["address_multiselect"] = fav["labels"]
                    st.rerun()
            with col_del:
                if st.button("✕", key="btn_del_fav", use_container_width=True):
                    delete_favorite(fav["id"])
                    st.rerun()

    # Save current selection as favorite
    with st.expander("Sauvegarder la sélection comme favori"):
        current_selection = st.session_state.get("address_multiselect", [])
        if not current_selection:
            st.caption("Aucune adresse sélectionnée.")
        else:
            fav_name_input = st.text_input(
                "Nom du favori",
                placeholder="Ex : Bâtiments rue de Rive",
                key="fav_name_input",
            )
            if st.button("Sauvegarder", key="btn_save_fav", use_container_width=True):
                if fav_name_input.strip():
                    ok = save_favorite(
                        fav_name_input.strip(),
                        current_selection,
                    )
                    if ok:
                        st.toast("Favori sauvegardé.")
                        st.rerun()
                    else:
                        st.warning("Ce groupe d'adresses est déjà dans vos favoris.")
                else:
                    st.warning("Saisissez un nom avant de sauvegarder.")

    st.divider()
    st.subheader("Historique des adresses")

    history_entries = load_history(n=20)

    if not history_entries:
        st.caption("Aucune adresse consultée pour l'instant.")
    else:
        for entry in history_entries:
            labels: list[str] = entry["labels"]
            # Affiche uniquement la partie adresse, sans le "(EGID)"
            label_short = ", ".join(a.split(" (")[0] for a in labels)
            # Timestamp formaté : "19.03.2026 14:32"
            ts_fmt = entry["ts"][:16].replace("T", " ")
            ts_fmt = f"{ts_fmt[8:10]}.{ts_fmt[5:7]}.{ts_fmt[:4]} {ts_fmt[11:16]}"

            col_label, col_del = st.columns([5, 1])
            with col_label:
                if st.button(
                    label_short,
                    key=f"history_{entry['id']}",
                    use_container_width=True,
                    help=ts_fmt,  # timestamp au survol
                ):
                    st.session_state["address_multiselect"] = labels
                    st.rerun()
            with col_del:
                if st.button(
                    "✕",
                    key=f"history_del_{entry['id']}",
                    use_container_width=True,
                ):
                    delete_history_entry(entry["id"])
                    st.rerun()

# ---------------------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------------------
st.subheader("Sélection adresse")

# CSS pour améliorer l'affichage des tags (multiselect) — permet à chaque tag de s'afficher
# en entier sans troncature, même avec du contenu long (ex: "Rue de Rive 10 (1234567)")
st.markdown(
    """
    <style>
    span[data-baseweb="tag"] { max-width: none !important; width: fit-content !important; }
    span[data-baseweb="tag"] > span:first-child {
        overflow: visible !important; white-space: nowrap !important;
        text-overflow: unset !important; max-width: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# st.expander custom CSS pour supprimer les bordures et ombres, mieux intégrer les sections
st.markdown(
    """
    <style>
        [data-testid="stExpander"] {
            border: none;
            box-shadow: none;
        }
        [data-testid="stExpander"] summary {
            border-bottom: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

df_addresses = get_all_addresses()

df_addresses = df_addresses.with_columns(
    pl.col("egid").cast(pl.Utf8).fill_null("N/A").alias("egid_str")
).with_columns((pl.col("adresse") + " (" + pl.col("egid_str") + ")").alias("display"))

display_options = df_addresses["display"].to_list()
options_map: dict[str, dict] = {
    row["display"]: {"adresse": row["adresse"], "egid": row["egid_str"]}
    for row in df_addresses.to_dicts()
}
# Reverse map: egid -> display label
egid_to_display: dict[str, str] = {v["egid"]: k for k, v in options_map.items()}

# External filter + bulk action buttons
col_search, col_all, col_clear = st.columns([6, 1, 1])

# Applique la réinitialisation du filtre demandée par Tout/Aucun
if "_pending_search_filter" in st.session_state:
    st.session_state["address_search_filter"] = st.session_state.pop(
        "_pending_search_filter"
    )

with col_search:
    search_filter = st.text_input(
        "Filtrer",
        placeholder="Taper pour filtrer les adresses...",
        label_visibility="collapsed",
        key="address_search_filter",
    )

# Apply filter on the full list
filtered_options = (
    [o for o in display_options if search_filter.lower() in o.lower()]
    if search_filter
    else display_options
)

with col_all:
    if st.button(
        "Tout",
        use_container_width=True,
        help="Ajouter les résultats filtrés à la sélection",
    ):
        current = set(st.session_state["address_multiselect"])
        st.session_state["address_multiselect"] = list(current | set(filtered_options))
        st.session_state["_pending_search_filter"] = ""
        st.rerun()

with col_clear:
    if st.button("Aucun", use_container_width=True, help="Vider la sélection"):
        st.session_state["address_multiselect"] = []
        st.session_state["_pending_search_filter"] = ""
        st.rerun()

# Transfer pending selection set by the address importer (runs before widget instantiation)
if "_pending_multiselect" in st.session_state:
    st.session_state["address_multiselect"] = st.session_state.pop(
        "_pending_multiselect"
    )

# Garantit que les valeurs sélectionnées sont toujours dans les options,
# même si le filtre texte actif les exclurait.
current_selection = st.session_state.get("address_multiselect", [])
visible_options = list(dict.fromkeys(current_selection + filtered_options))

selected_options = st.multiselect(
    label="Adresse",
    options=visible_options,  # ← liste filtrée : la dropdown reste stable lors des clics successifs
    placeholder="Sélectionner une ou plusieurs adresses...",
    key="address_multiselect",
    label_visibility="collapsed",
)

# Reverse map: adresse (lowercase) -> display label — pour la recherche insensible à la casse
adresse_to_display: dict[str, str] = {
    v["adresse"].lower(): k for k, v in options_map.items()
}

# Import rapide depuis une liste d'EGIDs
with st.expander("Charger depuis une liste d'adresses"):
    adresse_raw = st.text_area(
        "Adresses (une par ligne)",
        height=80,
        placeholder="Ex :\nRue de Rive 10\nRue du Rhône 5",
        key="adresse_import_textarea",
    )
    if st.button("Charger", key="btn_load_adresses", use_container_width=False):
        tokens = adresse_raw.splitlines()
        adresses_input = {t.strip() for t in tokens if t.strip()}

        matched = [
            adresse_to_display[a.lower()]
            for a in adresses_input
            if a.lower() in adresse_to_display
        ]
        not_found = {a for a in adresses_input if a.lower() not in adresse_to_display}

        if matched:
            # Use staging key — direct write after widget instantiation raises StreamlitAPIException
            st.session_state["_pending_multiselect"] = matched
            if not_found:
                st.warning(
                    f"{len(not_found)} adresse(s) non trouvée(s) dans la base locale : "
                    f"{', '.join(sorted(not_found))}"
                )
            st.rerun()
        else:
            st.warning("Aucune adresse correspondante trouvée dans la base locale.")

if selected_options:
    st.write(f"{len(selected_options)} adresse(s) sélectionnée(s)")
    selected_rows = [options_map[opt] for opt in selected_options]
    st.session_state["data_verif_idc"] = pl.DataFrame(selected_rows)
    save_history_entry(selected_options)

# ---------------------------------------------------------------------------------------
try:
    if selected_options and len(st.session_state.get("data_verif_idc", [])) > 0:
        egids = st.session_state["data_verif_idc"]["egid"].to_list()
        # ------------------------------------------------------------------
        # API cache in session_state — avoids re-fetching when the user only
        # toggles a checkbox or adjusts a sidebar parameter.
        # The cache is invalidated whenever the selected EGID set changes.
        # ------------------------------------------------------------------
        cache_key = tuple(sorted(egids))
        if st.session_state.get("_api_cache_key") != cache_key:
            with st.spinner("Chargement des données SITG..."):
                data_geometry, data_df = fetch_idc_data(
                    egids, URL_INDICE_MOYENNES_3_ANS
                )
            st.session_state["_api_cache_key"] = cache_key
            st.session_state["_api_geometry"] = data_geometry
            st.session_state["_api_df"] = data_df
        else:
            data_geometry = st.session_state["_api_geometry"]
            data_df = st.session_state["_api_df"]

        if data_geometry and data_df:
            geojson_data, centroid = convert_geometry_for_streamlit(data_geometry)

        #######################################################################
        st.divider()

        # Chiffres-clé
        st.subheader("Chiffres-clé")
        show_kpis(data_df, seuil=seuil, year_range=year_range)

        #######################################################################

        # Map
        st.subheader("Plan de situation")
        with st.expander("Afficher la carte", expanded=True):
            show_map(geojson_data, centroid)

        #######################################################################

        # Barplot
        st.subheader("Historique IDC")
        with st.expander("Afficher graphique", expanded=True):
            adresses_titre = st.session_state["data_verif_idc"]["adresse"].to_list()
            title = ", ".join(adresses_titre)
            create_barplot(data_df, title, seuil=seuil, year_range=year_range)

        #######################################################################

        # Données IDC détaillées
        st.subheader("Données IDC")
        show_dataframe(data_df, seuil=seuil, year_range=year_range)
    else:
        st.error("Pas de données disponibles pour le(s) EGID associé(s) à ce site.")
except Exception as e:
    st.error(f"Une erreur est survenue lors de l'analyse : {e}")
