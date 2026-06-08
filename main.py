# main.py

from datetime import datetime

import polars as pl
import streamlit as st

from sections.helpers.db import (
    delete_favorite,
    delete_history_entry,
    get_all_addresses,
    init_adresses_table,
    init_autorizations_table,
    init_favorites_table,
    init_history_table,
    load_autorizations_by_egids,
    load_favorites,
    load_history,
    refresh_db_at_startup_if_needed,
    save_favorite,
    save_history_entry,
)
from sections.helpers.idc_api import fetch_idc_data
from sections.helpers.idc_charts import create_barplot
from sections.helpers.idc_geo import convert_geometry_for_streamlit, show_map
from sections.helpers.idc_tables import show_dataframe, show_kpis

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

# --------------------------------------------------------------------------------------
FIELDS = "*"
URL_INDICE_MOYENNES_3_ANS = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/"
    "SCANE_INDICE_MOYENNES_3_ANS/FeatureServer/0/query"
)

CURRENT_YEAR = datetime.now().year

# Init DB au démarrage, session_state uniquement pour le reload sidebar
init_history_table()
init_favorites_table()
init_adresses_table()
init_autorizations_table()
refresh_db_at_startup_if_needed(URL_INDICE_MOYENNES_3_ANS)


if "address_multiselect" not in st.session_state:
    st.session_state["address_multiselect"] = []

# --------------------------------------------------------------------------------------
# Sidebar — analysis parameters
# --------------------------------------------------------------------------------------
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

    st.caption(
        "Sources : [SCANE_INDICE_MOYENNES_3_ANS](https://sitg.ge.ch/donnees/scane-indice-moyennes-3-ans)"
        " · [SIT_AUTOR_DOSSIER](https://sitg.ge.ch/donnees/sit-autor-dossier)."
        " · [CAD_BATIMENT_HORSOL](https://sitg.ge.ch/donnees/cad-batiment-horsol)"
    )

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
                if st.button("Charger", key="btn_load_fav", width="stretch"):
                    st.session_state["address_multiselect"] = fav["labels"]
                    st.rerun()
            with col_del:
                if st.button("✕", key="btn_del_fav", width="stretch"):
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
            if st.button("Sauvegarder", key="btn_save_fav", width="stretch"):
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
                    width="stretch",
                    help=ts_fmt,  # timestamp au survol
                ):
                    st.session_state["address_multiselect"] = labels
                    st.rerun()
            with col_del:
                if st.button(
                    "✕",
                    key=f"history_del_{entry['id']}",
                    width="stretch",
                ):
                    delete_history_entry(entry["id"])
                    st.rerun()

# --------------------------------------------------------------------------------------
# Main content
# --------------------------------------------------------------------------------------
st.subheader("Sélection adresse")

# CSS pour améliorer l'affichage des tags (multiselect) — permet à chaque tag
# de s'afficher en entier sans troncature, même avec du contenu long
# (ex: "Rue de Rive 10 (1234567)")
st.markdown(
    """
    <style>
    span[data-baseweb="tag"] {
        max-width: none !important;
        width: fit-content !important;
    }
    span[data-baseweb="tag"] > span:first-child {
        overflow: visible !important; white-space: nowrap !important;
        text-overflow: unset !important; max-width: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# st.expander custom CSS pour supprimer les bordures et ombres, mieux intégrer les
# sections
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
        width="stretch",
        help="Ajouter les résultats filtrés à la sélection",
    ):
        current = set(st.session_state["address_multiselect"])
        st.session_state["address_multiselect"] = list(current | set(filtered_options))
        st.session_state["_pending_search_filter"] = ""
        st.rerun()

with col_clear:
    if st.button("Aucun", width="stretch", help="Vider la sélection"):
        st.session_state["address_multiselect"] = []
        st.session_state["_pending_search_filter"] = ""
        st.rerun()

# Transfer pending selection set by the address importer
# (runs before widget instantiation)
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
    options=visible_options,  # ← liste filtrée : la dropdown stable si clics successifs
    placeholder="Sélectionner une ou plusieurs adresses...",
    key="address_multiselect",
    label_visibility="collapsed",
)

# Reverse map: adresse (lowercase) -> display label — pour la recherche
# insensible à la casse
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
    if st.button("Charger", key="btn_load_adresses", width="content"):
        tokens = adresse_raw.splitlines()
        adresses_input = {t.strip() for t in tokens if t.strip()}

        matched = [
            adresse_to_display[a.lower()]
            for a in adresses_input
            if a.lower() in adresse_to_display
        ]
        not_found = {a for a in adresses_input if a.lower() not in adresse_to_display}

        if matched:
            # Use staging key — direct write after widget instantiation
            #  raises StreamlitAPIException
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

# --------------------------------------------------------------------------------------
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

        st.divider()

        # Load autorization records once here so they can feed both the KPI
        # row and the detailed table below without a second DB round-trip.
        egids_int = tuple(int(e) for e in egids if e and e not in ("N/A", "", None))
        autor_records = load_autorizations_by_egids(egids_int) if egids_int else []

        # IDC sections — year_range-dependent, isolated so slider errors don't
        # prevent the autorizations section below from rendering.
        try:
            st.subheader("Chiffres-clé")
            show_kpis(
                data_df, seuil=seuil, year_range=year_range, autor_records=autor_records
            )

            st.subheader("Plan de situation")
            with st.expander("Afficher la carte", expanded=True):
                show_map(geojson_data, centroid)

            st.subheader("Historique IDC")
            adresses_titre = st.session_state["data_verif_idc"]["adresse"].to_list()
            title = ", ".join(adresses_titre)
            create_barplot(data_df, title, seuil=seuil, year_range=year_range)

            st.subheader("Données IDC")
            show_dataframe(data_df, seuil=seuil, year_range=year_range)
        except Exception as e:
            st.error(f"Erreur lors de l'affichage IDC : {e}")

        #######################################################################

        # Dossiers d'autorisation — independent of year_range slider
        st.divider()
        st.subheader("Dossiers d'autorisation")
        if egids_int:
            if autor_records:
                df_autor = pl.DataFrame(autor_records).with_columns(
                    pl.col("date_depot")
                    .cast(pl.Utf8)
                    .str.slice(0, 10)
                    .alias("date_depot"),
                    pl.col("egid").cast(pl.Utf8),
                )

                col_op, col_st = st.columns(2)
                with col_op:
                    ops = sorted(
                        df_autor["type_operation"].drop_nulls().unique().to_list()
                    )
                    selected_ops = st.multiselect(
                        "Type d'opération",
                        options=ops,
                        default=ops,
                        key="autor_filter_operation",
                    )
                with col_st:
                    statuts = sorted(df_autor["statut"].drop_nulls().unique().to_list())
                    selected_statuts = st.multiselect(
                        "Statut",
                        options=statuts,
                        default=statuts,
                        key="autor_filter_statut",
                    )

                if selected_ops:
                    df_autor = df_autor.filter(
                        pl.col("type_operation").is_in(selected_ops)
                    )
                if selected_statuts:
                    df_autor = df_autor.filter(pl.col("statut").is_in(selected_statuts))

                    st.dataframe(
                        df_autor.select(
                            [
                                "date_depot",
                                "egid",
                                "id_dossier",
                                "type_dossier",
                                "type_operation",
                                "statut",
                                "description",
                                "lien_sad",
                            ]
                        ),
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "date_depot": st.column_config.TextColumn("Date dépôt"),
                            "egid": st.column_config.TextColumn("EGID"),
                            "id_dossier": st.column_config.TextColumn("Dossier"),
                            "type_dossier": st.column_config.TextColumn("Type"),
                            "type_operation": st.column_config.TextColumn("Opération"),
                            "statut": st.column_config.TextColumn("Statut"),
                            "description": st.column_config.TextColumn("Description"),
                            "lien_sad": st.column_config.LinkColumn(
                                "Lien SAD", display_text="Consulter"
                            ),
                        },
                    )
                st.caption(
                    f"{len(df_autor):,} dossier(s) affiché(s) sur \
                    {len(autor_records):,}au total."
                )
            else:
                st.info(
                    "Aucun dossier d'autorisation trouvé pour ces bâtiments. "
                    "Les données sont mises à jour automatiquement au démarrage puis chaque jour."
                )
    else:
        st.warning(
            "Veuillez renseigner une ou plusieurs adresses pour afficher \
                les données IDC."
        )
except Exception as e:
    st.error(f"Une erreur est survenue lors de l'analyse : {e}")
