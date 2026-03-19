# /sections/helpers/idc_api.py

import json
import logging
from typing import Dict, List, Optional, Tuple, Union

import polars as pl
import requests


logging.basicConfig(level=logging.DEBUG)

# Columns to keep from the API response, in display order
RESULT_COLUMNS = [
    "egid",
    "annee",
    "indice",
    "sre",
    "adresse",
    "npa",
    "commune",
    "destination",
    "agent_energetique_1",
    "quantite_agent_energetique_1",
    "unite_agent_energetique_1",
    "agent_energetique_2",
    "quantite_agent_energetique_2",
    "unite_agent_energetique_2",
    "agent_energetique_3",
    "quantite_agent_energetique_3",
    "unite_agent_energetique_3",
    "date_debut_periode",
    "date_fin_periode",
    "date_saisie",
    "indice_moy2",
    "annees_concernees_moy_2",
    "indice_moy3",
    "annees_concernees_moy_3",
    "id_concessionnaire",
    "nbre_preneur",
]


def fetch_idc_data(
    egid: Union[int, List[int]],
    url: str,
    fields: str = "*",
    chunk_size: int = 1000,
    table_name: str = "SCANE_INDICE_MOYENNES_3_ANS",
) -> Tuple[Optional[List[Dict]], Optional[List[Dict]]]:
    """
    Single API call replacing the previous two separate make_request() calls.

    Fetches with returnGeometry=true so both geometry and tabular data
    are retrieved in one round-trip, then splits the result.

    Returns:
        (geometry_records, data_records) — both None on error.
        geometry_records: list of {attributes, geometry} dicts for show_map.
        data_records:     cleaned, deduplicated attribute dicts for charts/tables.
    """
    where_clause = (
        f"egid IN ({','.join(map(str, egid))})"
        if isinstance(egid, list)
        else f"egid={egid}"
    )
    params = {
        "where": where_clause,
        "outFields": fields,
        "returnGeometry": "true",
        "f": "json",
        "resultOffset": 0,
        "resultRecordCount": chunk_size,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "features" not in data:
            logging.warning(f"{table_name} → 'features' not found in response")
            return None, None

        features = data["features"]

        # Geometry records: keep raw attributes + geometry for show_map
        geometry_records = [
            {"attributes": f["attributes"], "geometry": f["geometry"]} for f in features
        ]

        # Tabular records: clean and deduplicate with Polars
        raw_records = [f["attributes"] for f in features]
        df = (
            pl.from_dicts(raw_records)
            .select(RESULT_COLUMNS)
            .with_columns(
                [
                    pl.col("date_debut_periode").cast(pl.Datetime("ms")),
                    pl.col("date_fin_periode").cast(pl.Datetime("ms")),
                    pl.col("date_saisie").cast(pl.Datetime("ms")),
                    pl.col("npa").cast(pl.Int64),
                    pl.col("quantite_agent_energetique_1").cast(pl.Float64),
                    pl.col("quantite_agent_energetique_2").cast(pl.Float64),
                    pl.col("quantite_agent_energetique_3").cast(pl.Float64),
                ]
            )
            # Keep only the most recent saisie per (egid, annee)
            .sort(["egid", "annee", "date_saisie"], descending=[False, False, True])
            .unique(subset=["egid", "annee"], keep="first")
            .sort(["egid", "annee"])
        )

        return geometry_records, df.to_dicts()

    except requests.exceptions.RequestException as e:
        logging.error(f"{table_name} → Request error: {e}")
    except json.JSONDecodeError:
        logging.error(f"{table_name} → JSON decode error")

    return None, None


# ---------------------------------------------------------------------------
# Backward-compatible wrapper — kept for any other callers in the project
def make_request(
    offset: int,
    fields: str,
    url: str,
    chunk_size: int,
    table_name: str,
    geometry: bool,
    egid: Union[int, List[int]],
) -> Optional[List[Dict]]:
    """Legacy wrapper around fetch_idc_data(). Prefer fetch_idc_data() for new code."""
    geo, data = fetch_idc_data(egid, url, fields, chunk_size, table_name)
    return geo if geometry else data
