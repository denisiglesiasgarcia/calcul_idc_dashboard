# /sections/helpers/idc_api.py

import logging

import polars as pl
from sitg_api import fetch_all
from sitg_api.idc import (
    RESULT_COLUMNS,
    validate_schema,
)

logging.basicConfig(level=logging.WARNING)

# Uppercase → lowercase rename map to handle SITG returning uppercase column names
_RENAME = {c.upper(): c for c in RESULT_COLUMNS}


def fetch_idc_data(
    egid: int | list[int],
    url: str,
    fields: str = "*",
    chunk_size: int = 1000,
    table_name: str = "SCANE_INDICE_MOYENNES_3_ANS",
) -> tuple[list[dict] | None, list[dict] | None]:
    """
    Fetch IDC data and geometry for one or more EGIDs.

    Returns (geometry_records, data_records) — both None on error.
    geometry_records: list of {attributes, geometry} dicts for show_map.
    data_records:     cleaned, deduplicated attribute dicts for charts/tables.
    """
    where_clause = (
        f"egid IN ({','.join(map(str, egid))})"
        if isinstance(egid, list)
        else f"egid={egid}"
    )

    try:
        features = fetch_all(
            url,
            where=where_clause,
            fields=fields,
            with_geometry=True,
            chunk_size=chunk_size,
            progress=False,
        )
    except Exception as e:
        logging.error(f"{table_name} → fetch error: {e}")
        return None, None

    if not features:
        return None, None

    geometry_records = [
        {"attributes": f["attributes"], "geometry": f.get("geometry")} for f in features
    ]

    df = pl.from_dicts([f["attributes"] for f in features])
    rename = {k: v for k, v in _RENAME.items() if k in df.columns}
    if rename:
        df = df.rename(rename)

    df = (
        df.select(RESULT_COLUMNS)
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
        .sort(["egid", "annee", "date_saisie"], descending=[False, False, True])
        .unique(subset=["egid", "annee"], keep="first")
        .sort(["egid", "annee"])
    )

    schema_errors = validate_schema(df)
    for err in schema_errors:
        logging.warning(f"{table_name} → schema mismatch: {err}")

    return geometry_records, df.to_dicts()


# ---------------------------------------------------------------------------
# Backward-compatible wrapper — kept for any other callers in the project
def make_request(
    offset: int,
    fields: str,
    url: str,
    chunk_size: int,
    table_name: str,
    geometry: bool,
    egid: int | list[int],
) -> list[dict] | None:
    """Legacy wrapper around fetch_idc_data(). Prefer fetch_idc_data() for new code."""
    geo, data = fetch_idc_data(egid, url, fields, chunk_size, table_name)
    return geo if geometry else data
