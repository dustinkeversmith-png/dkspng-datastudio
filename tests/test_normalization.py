import pandas as pd

from app.normalization import normalize_dataframe
from app.source_registry import get_source


def test_normalize_generic_csv_rows():
    source = get_source("generic_csv_sample")
    df = pd.DataFrame([
        {"year": 2024, "county": "Multnomah", "latitude": 45.5, "longitude": -122.6, "count": 3}
    ])

    rows = normalize_dataframe(source, df)

    assert len(rows) == 1
    assert rows[0]["year"] == 2024
    assert rows[0]["county"] == "Multnomah"
    assert rows[0]["latitude"] == 45.5
    assert rows[0]["longitude"] == -122.6
