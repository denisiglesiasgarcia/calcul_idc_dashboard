"""Unit tests for automatic startup DB refresh scheduling."""

import sqlite3
from datetime import datetime, timedelta, timezone

from sections.helpers import db


def _set_last_refresh(path, dt: datetime) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            INSERT INTO app_metadata (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            ("last_full_refresh_utc", dt.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


class TestRefreshDbAtStartupIfNeeded:
    def test_refreshes_when_no_previous_timestamp(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        db.init_adresses_table()
        db.init_autorizations_table()

        calls = {"addr": 0, "autor": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is True
        assert calls == {"addr": 1, "autor": 1}

    def test_skips_refresh_when_recent_and_not_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        db.init_adresses_table()
        db.init_autorizations_table()
        db.init_metadata_table()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
                (1, "Rue Test 1"),
            )
            conn.execute("INSERT INTO autorizations (egid) VALUES (?)", (1,))
            conn.commit()
        finally:
            conn.close()

        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc))

        calls = {"addr": 0, "autor": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is False
        assert calls == {"addr": 0, "autor": 0}

    def test_refreshes_when_last_refresh_is_older_than_a_day(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        db.init_adresses_table()
        db.init_autorizations_table()
        db.init_metadata_table()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
                (1, "Rue Test 1"),
            )
            conn.execute("INSERT INTO autorizations (egid) VALUES (?)", (1,))
            conn.commit()
        finally:
            conn.close()

        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc) - timedelta(days=2))

        calls = {"addr": 0, "autor": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is True
        assert calls == {"addr": 1, "autor": 1}

    def test_refreshes_when_tables_are_empty_even_with_recent_timestamp(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        db.init_adresses_table()
        db.init_autorizations_table()
        db.init_metadata_table()
        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc))

        calls = {"addr": 0, "autor": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is True
        assert calls == {"addr": 1, "autor": 1}
