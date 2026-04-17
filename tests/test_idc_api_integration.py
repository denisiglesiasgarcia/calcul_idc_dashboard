# tests/test_idc_api_integration.py
"""
Tests d'intégration sur l'API SITG publique.
Pas de mock — appels réels, pas de secrets requis.
Adresse de référence : "Rue de la Prairie 4", Genève.
"""

import polars as pl
import pytest
import requests

from sections.helpers.idc_api import fetch_idc_data, RESULT_COLUMNS

URL_SITG = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/"
    "SCANE_INDICE_MOYENNES_3_ANS/FeatureServer/0/query"
)
ADRESSE_TEST = "Rue de la Prairie 4"

# Schéma attendu après transformation dans fetch_idc_data
EXPECTED_SCHEMA = {
    "egid": pl.Int64,
    "annee": pl.Int64,
    "indice": pl.Float64,
    "sre": pl.Float64,
    "adresse": pl.String,
    "npa": pl.Int64,
    "commune": pl.String,
    "destination": pl.String,
    "agent_energetique_1": pl.String,
    "quantite_agent_energetique_1": pl.Float64,
    "unite_agent_energetique_1": pl.String,
    "date_debut_periode": pl.Datetime("ms"),
    "date_fin_periode": pl.Datetime("ms"),
    "date_saisie": pl.Datetime("ms"),
}


# ---------------------------------------------------------------------------
# Fixture : récupère l'EGID depuis l'API SITG pour l'adresse de référence
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def egid_prairie() -> int:
    """Résout l'EGID de l'adresse de test via l'API SITG."""
    resp = requests.get(
        URL_SITG,
        params={
            "where": f"adresse LIKE '{ADRESSE_TEST}%'",
            "outFields": "egid,adresse",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "f": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    features = resp.json().get("features", [])
    assert features, f"Aucune adresse trouvée pour '{ADRESSE_TEST}' dans l'API SITG"

    egid = features[0]["attributes"]["egid"]
    assert isinstance(egid, int), f"EGID attendu int, reçu {type(egid)}"
    return egid


@pytest.fixture(scope="module")
def api_result(egid_prairie):
    """Appel unique à fetch_idc_data, résultat partagé par tous les tests."""
    geometry_records, data_records = fetch_idc_data(egid_prairie, URL_SITG)
    return geometry_records, data_records


# ---------------------------------------------------------------------------
# Tests sur la réponse brute
# ---------------------------------------------------------------------------
class TestFetchReturnTypes:
    def test_geometry_is_list(self, api_result):
        geometry_records, _ = api_result
        assert isinstance(geometry_records, list), (
            "geometry_records doit être une liste"
        )

    def test_data_is_list(self, api_result):
        _, data_records = api_result
        assert isinstance(data_records, list), "data_records doit être une liste"

    def test_not_empty(self, api_result):
        geometry_records, data_records = api_result
        assert len(geometry_records) > 0, "Aucune géométrie retournée"
        assert len(data_records) > 0, "Aucune donnée retournée"

    def test_geometry_has_required_keys(self, api_result):
        geometry_records, _ = api_result
        for rec in geometry_records:
            assert "attributes" in rec, (
                "Clé 'attributes' manquante dans geometry_records"
            )
            assert "geometry" in rec, "Clé 'geometry' manquante dans geometry_records"

    def test_geometry_has_rings(self, api_result):
        geometry_records, _ = api_result
        for rec in geometry_records:
            assert "rings" in rec["geometry"], "Clé 'rings' manquante dans geometry"


# ---------------------------------------------------------------------------
# Tests sur le schéma du DataFrame
# ---------------------------------------------------------------------------
class TestDataSchema:
    @pytest.fixture(autouse=True)
    def df(self, api_result):
        _, data_records = api_result
        self.df = pl.from_dicts(data_records)

    def test_all_result_columns_present(self):
        missing = [c for c in RESULT_COLUMNS if c not in self.df.columns]
        assert not missing, f"Colonnes manquantes : {missing}"

    def test_column_dtypes(self):
        errors = []
        for col, expected_dtype in EXPECTED_SCHEMA.items():
            if col not in self.df.columns:
                errors.append(f"{col}: absent du DataFrame")
                continue
            actual = self.df[col].dtype
            if actual != expected_dtype:
                errors.append(f"{col}: attendu {expected_dtype}, obtenu {actual}")
        assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Tests sur la qualité des données
# ---------------------------------------------------------------------------
class TestDataQuality:
    @pytest.fixture(autouse=True)
    def df(self, api_result):
        _, data_records = api_result
        self.df = pl.from_dicts(data_records)

    def test_egid_not_null(self):
        assert self.df["egid"].null_count() == 0, "egid contient des nulls"

    def test_annee_not_null(self):
        assert self.df["annee"].null_count() == 0, "annee contient des nulls"

    def test_annee_plausible(self):
        """Les années doivent être dans une plage réaliste pour les données IDC."""
        assert self.df["annee"].min() >= 2000, "annee min < 2000"
        assert self.df["annee"].max() <= 2030, "annee max > 2030"

    def test_indice_positive(self):
        """IDC doit être strictement positif quand non-null."""
        indices = self.df["indice"].drop_nulls()
        assert (indices > 0).all(), "Des valeurs IDC négatives ou nulles détectées"

    def test_sre_positive(self):
        """SRE doit être strictement positive quand non-null."""
        sres = self.df["sre"].drop_nulls()
        assert (sres > 0).all(), "Des valeurs SRE négatives ou nulles détectées"

    def test_npa_geneve(self):
        """NPA doit correspondre à la région genevoise (1200–1299)."""
        npas = self.df["npa"].drop_nulls()
        assert ((npas >= 1200) & (npas <= 1299)).all(), (
            f"NPA hors plage genevoise : {npas.unique().to_list()}"
        )

    def test_adresse_contient_prairie(self):
        """L'adresse retournée doit correspondre à l'adresse de test."""
        adresses = self.df["adresse"].drop_nulls().unique().to_list()
        match = any("prairie" in a.lower() for a in adresses)
        assert match, f"Adresse 'prairie' non trouvée dans : {adresses}"

    def test_no_duplicate_egid_annee(self):
        """fetch_idc_data doit dédoublonner sur (egid, annee)."""
        n_total = len(self.df)
        n_unique = self.df.select(["egid", "annee"]).unique().height
        assert n_total == n_unique, (
            f"Doublons (egid, annee) détectés : {n_total} lignes, {n_unique} uniques"
        )

    def test_date_debut_before_date_fin(self):
        """date_debut_periode doit être antérieure à date_fin_periode."""
        invalid = self.df.filter(
            pl.col("date_debut_periode") >= pl.col("date_fin_periode")
        )
        assert len(invalid) == 0, f"{len(invalid)} ligne(s) avec date_debut >= date_fin"

    def test_agent_energetique_1_not_null(self):
        """L'agent principal doit toujours être renseigné."""
        assert self.df["agent_energetique_1"].null_count() == 0, (
            "agent_energetique_1 contient des nulls"
        )
