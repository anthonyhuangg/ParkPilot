import pytest

from application.services.helper_service import haversine


def test_haversine_zero_distance():
    lon, lat = 151.2069, -33.8726
    assert haversine(lon, lat, lon, lat) == pytest.approx(0.0, abs=1e-9)


def test_haversine_symmetry():
    a = (151.2069, -33.8726)  # Sydney
    b = (144.9631, -37.8136)  # Melbourne
    d1 = haversine(a[0], a[1], b[0], b[1])
    d2 = haversine(b[0], b[1], a[0], a[1])
    assert d1 == pytest.approx(d2, rel=1e-12, abs=1e-9)


def test_haversine_known_distance_sydney_melbourne():
    syd = (151.2093, -33.8688)
    mel = (144.9631, -37.8136)
    dist = haversine(syd[0], syd[1], mel[0], mel[1])
    assert dist == pytest.approx(713.43, abs=5.0)  # few km tolerance
