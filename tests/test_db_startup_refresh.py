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


def _init_all_tables():
    db.init_adresses_table()
    db.init_autorizations_table()
    db.init_idc_table()
    db.init_metadata_table()


def _noop_addr(url, **kwargs):
    return 1


def _noop_autor(**kwargs):
    return 1


def _noop_idc(url, **kwargs):
    return 1


class TestRefreshDbAtStartupIfNeeded:
    def test_refreshes_when_no_previous_timestamp(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        _init_all_tables()

        calls = {"addr": 0, "autor": 0, "idc": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url, **kw: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda **kw: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_idc_db",
            lambda url, **kw: calls.__setitem__("idc", calls["idc"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is True
        assert calls == {"addr": 1, "autor": 1, "idc": 1}

    def test_skips_refresh_when_recent_and_not_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        _init_all_tables()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
                (1, "Rue Test 1"),
            )
            conn.execute("INSERT INTO autorizations (egid) VALUES (?)", (1,))
            conn.execute("INSERT INTO idc_data (egid) VALUES (?)", (1,))
            conn.commit()
        finally:
            conn.close()

        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc))

        calls = {"addr": 0, "autor": 0, "idc": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url, **kw: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda **kw: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_idc_db",
            lambda url, **kw: calls.__setitem__("idc", calls["idc"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is False
        assert calls == {"addr": 0, "autor": 0, "idc": 0}

    def test_refreshes_when_last_refresh_is_older_than_a_day(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        _init_all_tables()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
                (1, "Rue Test 1"),
            )
            conn.execute("INSERT INTO autorizations (egid) VALUES (?)", (1,))
            conn.execute("INSERT INTO idc_data (egid) VALUES (?)", (1,))
            conn.commit()
        finally:
            conn.close()

        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc) - timedelta(days=2))

        calls = {"addr": 0, "autor": 0, "idc": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url, **kw: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda **kw: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_idc_db",
            lambda url, **kw: calls.__setitem__("idc", calls["idc"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is True
        assert calls == {"addr": 1, "autor": 1, "idc": 1}

    def test_skips_refresh_when_empty_but_within_cooldown(self, tmp_path, monkeypatch):
        # Empty tables + a very recent refresh must NOT re-trigger on every rerun;
        # the empty-retry cooldown suppresses it.
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        _init_all_tables()
        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc))

        calls = {"addr": 0, "autor": 0, "idc": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url, **kw: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda **kw: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_idc_db",
            lambda url, **kw: calls.__setitem__("idc", calls["idc"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is False
        assert calls == {"addr": 0, "autor": 0, "idc": 0}

    def test_refreshes_when_empty_and_cooldown_elapsed(self, tmp_path, monkeypatch):
        # Empty tables + last refresh older than the cooldown → retry once.
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        _init_all_tables()
        _set_last_refresh(
            db.DB_PATH,
            datetime.now(timezone.utc) - db._EMPTY_RETRY_COOLDOWN - timedelta(minutes=1),
        )

        calls = {"addr": 0, "autor": 0, "idc": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url, **kw: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda **kw: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_idc_db",
            lambda url, **kw: calls.__setitem__("idc", calls["idc"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is True
        assert calls == {"addr": 1, "autor": 1, "idc": 1}

    def test_skips_refresh_when_only_idc_empty_but_within_cooldown(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "idc_test.db")
        _init_all_tables()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO adresses_egid (egid, adresse) VALUES (?, ?)",
                (1, "Rue Test 1"),
            )
            conn.execute("INSERT INTO autorizations (egid) VALUES (?)", (1,))
            # idc_data intentionally left empty
            conn.commit()
        finally:
            conn.close()

        _set_last_refresh(db.DB_PATH, datetime.now(timezone.utc))

        calls = {"addr": 0, "autor": 0, "idc": 0}
        monkeypatch.setattr(
            db,
            "refresh_adresses_db",
            lambda url, **kw: calls.__setitem__("addr", calls["addr"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_autorizations_db",
            lambda **kw: calls.__setitem__("autor", calls["autor"] + 1) or 1,
        )
        monkeypatch.setattr(
            db,
            "refresh_idc_db",
            lambda url, **kw: calls.__setitem__("idc", calls["idc"] + 1) or 1,
        )

        refreshed = db.refresh_db_at_startup_if_needed("http://fake")

        assert refreshed is False
        assert calls == {"addr": 0, "autor": 0, "idc": 0}
