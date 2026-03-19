# /sections/helpers/db.py

import json
import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

import polars as pl
import requests


logging.basicConfig(level=logging.DEBUG)


def refresh_adresses_db(
    url: str,
    db_path: str = "adresses_egid.db",
    chunk_size: int = 2000,
    max_workers: int = 3,
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Fetch all unique address/EGID pairs from the SITG API and rebuild the
    local SQLite database from scratch.

    Performance strategy:
      - Fetch total count first, then compute all page offsets upfront.
      - Fetch pages in parallel via ThreadPoolExecutor (3 workers — SITG throttles
        aggressively above ~4 concurrent connections).
      - Each page retries up to 4 times with exponential backoff on timeout/error.
      - Collect all records in memory, deduplicate with Polars, then do a
        single bulk INSERT in one transaction.

    Args:
        url:          SITG API endpoint.
        db_path:      Path to the local SQLite database.
        chunk_size:   Records per API page (max 2000 for ArcGIS hosted services).
        max_workers:  Parallel HTTP threads. Keep at 3 to stay under SITG rate limit.
        progress_bar: Optional st.progress placeholder for visual feedback.
        status_text:  Optional st.empty placeholder for status messages.

    Returns the total number of unique records saved.
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logging.info(f"refresh_adresses_db → {msg}")

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    # --- Step 1: total count ---
    _status("Connexion au SITG — récupération du nombre total d'adresses...")
    _progress(0.0)

    try:
        resp = requests.get(
            url,
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            timeout=30,
        )
        resp.raise_for_status()
        total_count = resp.json().get("count", 0)
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        raise RuntimeError(
            f"Impossible de récupérer le nombre total d'adresses: {e}"
        ) from e

    _status(
        f"{total_count:,} adresses trouvées — téléchargement en parallèle ({max_workers} workers)..."
    )

    offsets = list(range(0, total_count, chunk_size))
    completed_pages = 0
    lock = threading.Lock()
    all_records: list[tuple] = []

    # --- Step 2: fetch pages in parallel with retry/backoff ---
    def fetch_page(offset: int) -> list[tuple]:
        """
        Fetch one page with up to 4 retries and exponential backoff.
        Backoff: 2s, 4s, 8s, 16s — gives the API time to recover after throttling.
        """
        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    params={
                        "where": "1=1",
                        "outFields": "adresse,egid",
                        "returnGeometry": "false",
                        "f": "json",
                        "resultOffset": offset,
                        "resultRecordCount": chunk_size,
                    },
                    timeout=60,  # generous timeout — SITG can be slow under load
                )
                response.raise_for_status()
                features = response.json().get("features", [])
                return [
                    (f["attributes"]["egid"], f["attributes"]["adresse"])
                    for f in features
                    if f["attributes"].get("egid") and f["attributes"].get("adresse")
                ]
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** (attempt + 1)  # 2, 4, 8, 16 seconds
                logging.warning(
                    f"fetch_page offset={offset} attempt {attempt + 1}/{max_retries} "
                    f"failed ({e}), retrying in {wait}s..."
                )
                time.sleep(wait)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_page, off): off for off in offsets}
        for future in as_completed(futures):
            offset = futures[future]
            try:
                records = future.result()
            except Exception as e:
                raise RuntimeError(
                    f"Échec du téléchargement à l'offset {offset}: {e}"
                ) from e

            with lock:
                all_records.extend(records)
                completed_pages += 1
                progress_value = completed_pages / len(offsets)
                _progress(progress_value * 0.9)  # reserve last 10% for DB write
                _status(
                    f"Téléchargé {len(all_records):,} / ~{total_count:,} adresses "
                    f"({progress_value * 100:.0f}%)"
                )

    # --- Step 3: deduplicate with Polars ---
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

    # --- Step 4: rebuild table and bulk insert in one transaction ---
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS adresses_egid")
    conn.execute("""
        CREATE TABLE adresses_egid (
            egid    INTEGER NOT NULL,
            adresse TEXT    NOT NULL,
            PRIMARY KEY (egid, adresse)
        )
    """)
    conn.execute("CREATE INDEX idx_adresse ON adresses_egid (adresse)")
    conn.execute("BEGIN")
    conn.executemany(
        "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
        unique_records,
    )
    conn.execute("COMMIT")
    conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(unique_records):,} adresses uniques enregistrées.")
    return len(unique_records)

# ---------------------------------------------------------------------------
# Historique des consultations
# ---------------------------------------------------------------------------

def init_history_table(db_path: str = "adresses_egid.db") -> None:
    """
    Crée la table d'historique si elle n'existe pas.
    Appelée au démarrage de l'application — idempotente.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consultation_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         TEXT    NOT NULL,  -- ISO timestamp
            labels     TEXT    NOT NULL   -- JSON array of display labels (adresse + egid)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_ts ON consultation_history (ts DESC)
    """)
    conn.commit()
    conn.close()


def save_history_entry(
    selected_options: list[str],
    db_path: str = "adresses_egid.db",
) -> None:
    """
    Sauvegarde un groupe d'adresses sélectionnées dans l'historique.
    Dédoublonne sur le contenu — ne réinsère pas si le dernier enregistrement
    est identique à la sélection courante.
    """
    labels_json = json.dumps(selected_options, ensure_ascii=False)
    conn = sqlite3.connect(db_path)

    # Evite les doublons consécutifs (même sélection rechargée)
    last = conn.execute(
        "SELECT labels FROM consultation_history ORDER BY ts DESC LIMIT 1"
    ).fetchone()

    if last is None or last[0] != labels_json:
        conn.execute(
            "INSERT INTO consultation_history (ts, labels) VALUES (?, ?)",
            (datetime.utcnow().isoformat(), labels_json),
        )
        conn.commit()
    conn.close()


def load_history(
    n: int = 20,
    db_path: str = "adresses_egid.db",
) -> list[dict]:
    """
    Retourne les n dernières entrées de l'historique, ordre antéchronologique.
    Chaque entrée : {"id": int, "ts": str, "labels": list[str]}
    """
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, ts, labels FROM consultation_history ORDER BY ts DESC LIMIT ?",
        (n,),
    ).fetchall()
    conn.close()
    return [
        {"id": row[0], "ts": row[1], "labels": json.loads(row[2])}
        for row in rows
    ]


def delete_history_entry(
    entry_id: int,
    db_path: str = "adresses_egid.db",
) -> None:
    """Supprime une entrée d'historique par son id."""
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM consultation_history WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()