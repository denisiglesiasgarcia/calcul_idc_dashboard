"""Unit tests for idc_api.fetch_idc_data() with mocked HTTP requests."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from sections.helpers.idc_api import RESULT_COLUMNS, fetch_idc_data

_TS = 1_672_531_200_000  # 2023-01-01 00:00:00 UTC as ms epoch


def _make_feature(egid: int = 100, annee: int = 2022, saisie_ts: int = _TS) -> dict:
    attrs = {
        "egid": egid,
        "annee": annee,
        "indice": 300,
        "sre": 500,
        "adresse": f"Rue Test {egid}",
        "npa": 1201,
        "commune": "Genève",
        "destination": "Habitation",
        "agent_energetique_1": "gaz",
        "quantite_agent_energetique_1": 100.0,
        "unite_agent_energetique_1": "kWh",
        "agent_energetique_2": None,
        "quantite_agent_energetique_2": None,
        "unite_agent_energetique_2": None,
        "agent_energetique_3": None,
        "quantite_agent_energetique_3": None,
        "unite_agent_energetique_3": None,
        "date_debut_periode": saisie_ts,
        "date_fin_periode": saisie_ts,
        "date_saisie": saisie_ts,
        "indice_moy2": None,
        "annees_concernees_moy_2": None,
        "indice_moy3": None,
        "annees_concernees_moy_3": None,
        "id_concessionnaire": None,
        "nbre_preneur": None,
    }
    return {
        "attributes": attrs,
        "geometry": {
            "rings": [[[2499000, 1117000], [2499100, 1117000], [2499000, 1117000]]]
        },
    }


def _ok_response(features: list) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"features": features}
    mock.raise_for_status.return_value = None
    return mock


class TestFetchIdcDataSuccess:
    def test_returns_two_element_tuple(self):
        with patch("requests.get", return_value=_ok_response([_make_feature()])):
            result = fetch_idc_data(100, "http://fake")
        assert len(result) == 2

    def test_geometry_and_data_not_none(self):
        with patch("requests.get", return_value=_ok_response([_make_feature()])):
            geo, data = fetch_idc_data(100, "http://fake")
        assert geo is not None
        assert data is not None

    def test_geometry_contains_attributes_and_geometry_keys(self):
        with patch("requests.get", return_value=_ok_response([_make_feature()])):
            geo, _ = fetch_idc_data(100, "http://fake")
        assert len(geo) == 1
        assert "attributes" in geo[0]
        assert "geometry" in geo[0]

    def test_data_row_contains_all_result_columns(self):
        with patch("requests.get", return_value=_ok_response([_make_feature()])):
            _, data = fetch_idc_data(100, "http://fake")
        row = data[0]
        for col in RESULT_COLUMNS:
            assert col in row, f"Missing column: {col}"

    def test_multiple_buildings_returned(self):
        features = [_make_feature(egid=1), _make_feature(egid=2)]
        with patch("requests.get", return_value=_ok_response(features)):
            geo, data = fetch_idc_data([1, 2], "http://fake")
        assert len(geo) == 2
        assert len(data) == 2

    def test_deduplication_keeps_most_recent_saisie(self):
        old_ts = 1_000_000_000_000
        new_ts = 1_672_531_200_000
        features = [
            _make_feature(egid=1, annee=2022, saisie_ts=old_ts),
            _make_feature(egid=1, annee=2022, saisie_ts=new_ts),
        ]
        with patch("requests.get", return_value=_ok_response(features)):
            _, data = fetch_idc_data(1, "http://fake")
        assert len(data) == 1

    def test_different_years_not_deduplicated(self):
        features = [
            _make_feature(egid=1, annee=2021),
            _make_feature(egid=1, annee=2022),
        ]
        with patch("requests.get", return_value=_ok_response(features)):
            _, data = fetch_idc_data(1, "http://fake")
        assert len(data) == 2

    def test_list_egid_builds_in_clause(self):
        with patch("requests.get", return_value=_ok_response([_make_feature()])) as mock_get:
            fetch_idc_data([1, 2], "http://fake")
        where = mock_get.call_args[1]["params"]["where"]
        assert "IN" in where
        assert "1" in where
        assert "2" in where

    def test_single_egid_builds_eq_clause(self):
        with patch("requests.get", return_value=_ok_response([_make_feature()])) as mock_get:
            fetch_idc_data(100, "http://fake")
        where = mock_get.call_args[1]["params"]["where"]
        assert "egid=100" in where

    def test_result_sorted_by_egid_and_annee(self):
        features = [
            _make_feature(egid=2, annee=2022),
            _make_feature(egid=1, annee=2021),
            _make_feature(egid=1, annee=2022),
        ]
        with patch("requests.get", return_value=_ok_response(features)):
            _, data = fetch_idc_data([1, 2], "http://fake")
        egids = [r["egid"] for r in data]
        annees = [r["annee"] for r in data]
        assert egids == sorted(egids)
        assert annees[:2] == sorted(annees[:2])  # first two rows share egid=1


class TestFetchIdcDataErrors:
    def test_connection_error_returns_none_none(self):
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("err")):
            geo, data = fetch_idc_data(1, "http://fake")
        assert geo is None
        assert data is None

    def test_timeout_returns_none_none(self):
        with patch("requests.get", side_effect=requests.exceptions.Timeout()):
            geo, data = fetch_idc_data(1, "http://fake")
        assert geo is None
        assert data is None

    def test_http_error_returns_none_none(self):
        mock = MagicMock()
        mock.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        with patch("requests.get", return_value=mock):
            geo, data = fetch_idc_data(1, "http://fake")
        assert geo is None
        assert data is None

    def test_missing_features_key_returns_none_none(self):
        mock = _ok_response([])
        mock.json.return_value = {"error": "not found"}
        with patch("requests.get", return_value=mock):
            geo, data = fetch_idc_data(1, "http://fake")
        assert geo is None
        assert data is None

    def test_json_decode_error_returns_none_none(self):
        mock = MagicMock()
        mock.raise_for_status.return_value = None
        mock.json.side_effect = json.JSONDecodeError("err", "", 0)
        with patch("requests.get", return_value=mock):
            geo, data = fetch_idc_data(1, "http://fake")
        assert geo is None
        assert data is None
