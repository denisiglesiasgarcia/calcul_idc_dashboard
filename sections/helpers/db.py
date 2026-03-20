# /sections/helpers/db.py

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import polars as pl
import psycopg2
from psycopg2.extras import execute_values
import requests
import streamlit as st

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_conn(statement_timeout_ms: int = 30_000):
    """Open a psycopg2 connection using Streamlit secrets.

    statement_timeout_ms: per-connection timeout in ms.
    Use a higher value for bulk write operations.
    """
    s = st.secrets["supabase"]
    return psycopg2.connect(
        host=s["host"],
        port=s["port"],
        dbname=s["dbname"],
        user=s["user"],
        password=s["password"],
        sslmode="require",
        options=f"-c statement_timeout={statement_timeout_ms}",
    )


def _execute(conn, sql: str, params=None) -> None:
    """Execute a single statement via cursor. Always pass a connection, not a cursor."""
    cur = conn.cursor()
    cur.execute(sql, params)
    cur.close()


# ---------------------------------------------------------------------------
# Schema init — idempotent, called at app startup
# ---------------------------------------------------------------------------


def init_history_table() -> None:
    conn = _get_conn()
    with conn:
        _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS consultation_history (
                id     SERIAL PRIMARY KEY,
                ts     TEXT NOT NULL,
                labels TEXT NOT NULL
            )
        """,
        )
        _execute(
            conn,
            """
            CREATE INDEX IF NOT EXISTS idx_history_ts
            ON consultation_history (ts DESC)
        """,
        )
    conn.close()


def init_favorites_table() -> None:
    conn = _get_conn()
    with conn:
        _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS adresses_favorites (
                id     SERIAL PRIMARY KEY,
                name   TEXT NOT NULL,
                labels TEXT NOT NULL UNIQUE
            )
        """,
        )
    conn.close()


# ---------------------------------------------------------------------------
# Address cache
# ---------------------------------------------------------------------------


def refresh_adresses_db(
    url: str,
    chunk_size: int = 2000,
    max_workers: int = 3,
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Fetch all address/EGID pairs from SITG and rebuild the Supabase table.
    Strategy: parallel fetch with retry, then bulk insert in chunks of 1000.
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logger.info(msg)

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    # Step 1: total count
    _status("Connexion au SITG — récupération du nombre total d'adresses...")
    _progress(0.0)

    resp = requests.get(
        url,
        params={
            "where": "1=1",
            "outFields": "adresse,egid",
            "returnDistinctValues": "true",
            "returnGeometry": "false",
            "returnCountOnly": "true",
            "f": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    total_count = resp.json().get("count", 0)
    _status(f"{total_count:,} adresses trouvées — téléchargement...")

    offsets = list(range(0, total_count, chunk_size))
    completed_pages = 0
    lock = threading.Lock()
    all_records: list[tuple] = []

    def fetch_page(offset: int) -> list[tuple]:
        for attempt in range(4):
            try:
                r = requests.get(
                    url,
                    params={
                        "where": "1=1",
                        "outFields": "adresse,egid",
                        "returnDistinctValues": "true",
                        "returnGeometry": "false",
                        "f": "json",
                        "resultOffset": offset,
                        "resultRecordCount": chunk_size,
                    },
                    timeout=60,
                )
                r.raise_for_status()
                features = r.json().get("features", [])
                return [
                    (f["attributes"]["egid"], f["attributes"]["adresse"])
                    for f in features
                    if f["attributes"].get("egid") and f["attributes"].get("adresse")
                ]
            except requests.exceptions.RequestException:
                if attempt == 3:
                    raise
                wait = 2 ** (attempt + 1)
                logger.warning(
                    f"offset={offset} attempt {attempt + 1}/4 failed, retry in {wait}s"
                )
                time.sleep(wait)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_page, off): off for off in offsets}
        for future in as_completed(futures):
            offset = futures[future]
            try:
                records = future.result()
            except Exception as e:
                raise RuntimeError(f"Échec offset {offset}: {e}") from e
            with lock:
                all_records.extend(records)
                completed_pages += 1
                frac = completed_pages / len(offsets)
                _progress(frac * 0.9)
                _status(f"Téléchargé {len(all_records):,} / ~{total_count:,} adresses")

    # Step 2: deduplicate with Polars
    _status("Dédoublonnage et écriture en base...")
    df = (
        pl.DataFrame(
            {
                "egid": [r[0] for r in all_records],
                "adresse": [r[1] for r in all_records],
            }
        )
        .unique()
        .sort("adresse")
    )
    unique_records = df.rows()

    # Step 3: truncate and bulk insert with execute_values
    conn = _get_conn(statement_timeout_ms=300_000)
    with conn:
        _execute(conn, "TRUNCATE TABLE adresses_egid")
        cur = conn.cursor()
        chunk = 1000
        total_chunks = (len(unique_records) + chunk - 1) // chunk
        for idx, i in enumerate(range(0, len(unique_records), chunk)):
            execute_values(
                cur,
                "INSERT INTO adresses_egid (egid, adresse) VALUES %s ON CONFLICT DO NOTHING",
                unique_records[i : i + chunk],
            )
            # Map DB write progress to the last 10% (0.9 → 1.0)
            write_frac = (idx + 1) / total_chunks
            _progress(0.9 + write_frac * 0.1)
            _status(
                f"Écriture en base : {min(i + chunk, len(unique_records)):,} / {len(unique_records):,} adresses"
            )
        cur.close()
    conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(unique_records):,} adresses uniques enregistrées.")
    return len(unique_records)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def save_history_entry(selected_options: list[str]) -> None:
    labels_json = json.dumps(sorted(selected_options), ensure_ascii=False)
    conn = _get_conn()
    with conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM consultation_history WHERE labels = %s", (labels_json,)
        )
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO consultation_history (ts, labels) VALUES (%s, %s)",
                (datetime.utcnow().isoformat(), labels_json),
            )
        cur.close()
    conn.close()


def load_history(n: int = 20) -> list[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ts, labels FROM consultation_history ORDER BY ts DESC LIMIT %s",
        (n,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "ts": r[1], "labels": json.loads(r[2])} for r in rows]


def delete_history_entry(entry_id: int) -> None:
    conn = _get_conn()
    with conn:
        _execute(conn, "DELETE FROM consultation_history WHERE id = %s", (entry_id,))
    conn.close()


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------


def save_favorite(name: str, labels: list[str]) -> bool:
    labels_json = json.dumps(sorted(labels), ensure_ascii=False)
    conn = _get_conn()
    try:
        with conn:
            _execute(
                conn,
                "INSERT INTO adresses_favorites (name, labels) VALUES (%s, %s)",
                (name, labels_json),
            )
        return True
    except psycopg2.errors.UniqueViolation:
        return False
    finally:
        conn.close()


def load_favorites() -> list[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, labels FROM adresses_favorites ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "labels": json.loads(r[2])} for r in rows]


def delete_favorite(fav_id: int) -> None:
    conn = _get_conn()
    with conn:
        _execute(conn, "DELETE FROM adresses_favorites WHERE id = %s", (fav_id,))
    conn.close()


# ---------------------------------------------------------------------------
# Address selector
# ---------------------------------------------------------------------------


@st.cache_data
def get_all_addresses() -> pl.DataFrame:
    """Load address/EGID pairs from Supabase, sorted by address."""
    conn = _get_conn()
    try:
        return pl.read_database(
            query="SELECT DISTINCT adresse, egid FROM adresses_egid ORDER BY adresse",
            connection=conn,
        )
    except Exception as e:
        logger.error(f"get_all_addresses failed: {e}")
        return pl.DataFrame(
            {
                "adresse": pl.Series([], dtype=pl.Utf8),
                "egid": pl.Series([], dtype=pl.Utf8),
            }
        )
    finally:
        conn.close()
