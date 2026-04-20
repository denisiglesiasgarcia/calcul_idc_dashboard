"""Unit tests for idc_geo.convert_geometry_for_streamlit() — coordinate transform."""

import pytest

from sections.helpers.idc_geo import convert_geometry_for_streamlit

# Geneva area in LV95 (EPSG:2056) — approximately lon=6.15, lat=46.20
_GENEVA_RING = [
    [2499000, 1117000],
    [2499100, 1117000],
    [2499100, 1117100],
    [2499000, 1117100],
    [2499000, 1117000],  # closed ring
]


@pytest.fixture
def single_building():
    return [
        {
            "geometry": {"rings": [_GENEVA_RING]},
            "attributes": {"egid": 12345, "adresse": "Rue Test 1"},
        }
    ]


def test_returns_geojson_feature_collection(single_building):
    geojson, _ = convert_geometry_for_streamlit(single_building)
    assert isinstance(geojson, dict)
    assert geojson["type"] == "FeatureCollection"
    assert "features" in geojson


def test_returns_centroid_with_two_coords(single_building):
    _, centroid = convert_geometry_for_streamlit(single_building)
    assert len(centroid) == 2


def test_feature_count_matches_input(single_building):
    geojson, _ = convert_geometry_for_streamlit(single_building)
    assert len(geojson["features"]) == 1


def test_feature_has_required_keys(single_building):
    geojson, _ = convert_geometry_for_streamlit(single_building)
    f = geojson["features"][0]
    assert f["type"] == "Feature"
    assert "geometry" in f
    assert "properties" in f
    assert f["geometry"]["type"] == "Polygon"


def test_coordinates_converted_to_wgs84(single_building):
    geojson, _ = convert_geometry_for_streamlit(single_building)
    ring = geojson["features"][0]["geometry"]["coordinates"][0]
    lons = [pt[0] for pt in ring]
    lats = [pt[1] for pt in ring]
    # Geneva area bounding box in WGS84
    assert all(5.5 < lon < 7.5 for lon in lons)
    assert all(45.5 < lat < 47.5 for lat in lats)


def test_centroid_within_geneva_bounds(single_building):
    _, centroid = convert_geometry_for_streamlit(single_building)
    lon, lat = float(centroid[0]), float(centroid[1])
    assert 5.5 < lon < 7.5
    assert 45.5 < lat < 47.5


def test_item_without_geometry_key_skipped():
    data = [
        {"attributes": {"egid": 1}},  # no geometry
        {
            "geometry": {"rings": [_GENEVA_RING]},
            "attributes": {"egid": 2},
        },
    ]
    geojson, _ = convert_geometry_for_streamlit(data)
    assert len(geojson["features"]) == 1
    assert geojson["features"][0]["properties"]["egid"] == 2


def test_item_with_geometry_but_no_rings_skipped():
    data = [
        {"geometry": {}, "attributes": {"egid": 1}},  # geometry present but no rings
        {
            "geometry": {"rings": [_GENEVA_RING]},
            "attributes": {"egid": 2},
        },
    ]
    geojson, _ = convert_geometry_for_streamlit(data)
    assert len(geojson["features"]) == 1


def test_multiple_buildings_all_converted():
    data = [
        {"geometry": {"rings": [_GENEVA_RING]}, "attributes": {"egid": i}}
        for i in range(3)
    ]
    geojson, _ = convert_geometry_for_streamlit(data)
    assert len(geojson["features"]) == 3


def test_attributes_preserved_in_properties(single_building):
    geojson, _ = convert_geometry_for_streamlit(single_building)
    props = geojson["features"][0]["properties"]
    assert props["egid"] == 12345
    assert props["adresse"] == "Rue Test 1"


def test_ring_is_closed_after_conversion(single_building):
    geojson, _ = convert_geometry_for_streamlit(single_building)
    ring = geojson["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]  # first == last → closed ring


def test_multiple_rings_per_building():
    data = [
        {
            "geometry": {"rings": [_GENEVA_RING, _GENEVA_RING]},
            "attributes": {"egid": 1},
        }
    ]
    geojson, _ = convert_geometry_for_streamlit(data)
    coords = geojson["features"][0]["geometry"]["coordinates"]
    assert len(coords) == 2
