from app.querying import query_observations


def test_query_observations_function_exists():
    assert callable(query_observations)
