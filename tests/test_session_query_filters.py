from app.session_query_filters import effective_observation_filters


def test_explicit_kwargs_override_profile():
    base = effective_observation_filters(
        session_profile={"latitude": 1.0, "longitude": 2.0, "radius_km": 100},
        source_profile={"radius_km": 50},
        latitude=None,
        longitude=None,
        radius_km=25,
    )
    assert base["latitude"] == 1.0
    assert base["longitude"] == 2.0
    assert base["radius_km"] == 25
