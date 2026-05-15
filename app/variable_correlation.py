import pandas as pd
from sqlalchemy.orm import Session
from app.session_query import resolve_observation_rows


def selected_variable_correlation(
    db: Session,
    variables: list[str],
    source_key: str | None = None,
    session_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
):
    if len(variables) < 2:
        return {"status": "failed", "error": "Choose at least 2 variables."}

    if len(variables) > 5:
        return {"status": "failed", "error": "Choose at most 5 variables."}

    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=10000,
    )

    df = pd.DataFrame(rows)

    # Pull values from normal columns or raw_properties_json.
    output = pd.DataFrame()

    for variable in variables:
        if variable in df.columns:
            output[variable] = pd.to_numeric(df[variable], errors="coerce")
        else:
            output[variable] = pd.to_numeric(
                df["raw_properties_json"].apply(
                    lambda props: props.get(variable) if isinstance(props, dict) else None
                ),
                errors="coerce",
            )

    output = output.dropna(axis=1, how="all")

    if output.shape[1] < 2:
        return {
            "status": "failed",
            "error": "Not enough numeric variables found.",
            "variables": variables,
        }

    corr = output.corr().fillna(0)

    return {
        "status": "success",
        "variables": list(corr.columns),
        "matrix": corr.values.tolist(),
        "row_count": len(output),
    }