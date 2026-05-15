from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analysis import correlation_analysis, county_compare_analysis, regression_analysis
from app.comparison import build_sankey, comparison_presets, cross_domain_compare
from app.db import get_db
from app.exports import rows_to_csv_response
from app.ingestion import ingest_source
from app.matlab_modeling import matrix_compare_model, risk_surface_model, spatial_interpolation_model
from app.querying import list_regions, query_observations
from app.schemas import (
    AddDatasetRequest,
    BufferApplyRequest,
    BufferCommandRequest,
    ChartUpsertRequest,
    CreateSessionRequest,
    DatasetVerifyResult,
    IngestionResult,
    PipelineUpdateRequest,
    SnapshotAppendRequest,
    SourceRegistryUpsertRequest,
    SourceDefinition,
    VisualizationSessionSummary,
)
from app.session_query import fetch_session_observations, resolve_observation_rows, verify_session_dataset
from app.source_registry import add_or_update_source, delete_source, get_source, list_sources
from app.trends import dataset_trends
from app.variable_correlation import selected_variable_correlation
from app.data_manipulation import validate_pipeline_steps
from fastapi.middleware.cors import CORSMiddleware
from app.comparison import compare_datasets
from app.chart_specs import validate_chart_definition, validate_save_snapshot
from app.workflow.session_pipeline import SessionPipeline
from app.visualization_session import (
    VisualizationSession,
    add_dataset,
    append_buffer_command,
    append_chart_definition,
    append_saved_snapshot,
    apply_buffer_to_pipeline,
    clear_buffer,
    clear_charts,
    clear_saved_snapshots,
    create_session,
    delete_session,
    get_buffer,
    get_session,
    remove_dataset,
    set_pipeline,
)


app = FastAPI(title="Regional Data Studio API", version="0.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/sources", response_model=list[SourceDefinition])
def sources():
    return list_sources()


@app.post("/sources", response_model=SourceDefinition)
def source_upsert(body: SourceRegistryUpsertRequest):
    source = SourceDefinition.model_validate(body.model_dump())
    return add_or_update_source(source)


@app.delete("/sources/{source_key}")
def source_delete(source_key: str):
    try:
        delete_source(source_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "source_key": source_key}


def _session_summary(session: VisualizationSession) -> VisualizationSessionSummary:
    return VisualizationSessionSummary(
        session_id=session.session_id,
        label=session.label,
        datasets={did: b.source_key for did, b in session.datasets.items()},
        pipeline_step_count=len(session.pipeline),
        buffer_step_count=len(session.command_buffer),
        chart_count=len(session.chart_definitions),
        saved_snapshot_count=len(session.saved_snapshots),
    )


@app.post("/session", response_model=VisualizationSessionSummary)
def session_create(body: CreateSessionRequest | None = None):
    session = create_session(label=body.label if body else None)
    return _session_summary(session)


@app.get("/session/{session_id}", response_model=VisualizationSessionSummary)
def session_get(session_id: str):
    try:
        return _session_summary(get_session(session_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/session/{session_id}")
def session_remove(session_id: str):
    try:
        delete_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "session_id": session_id}


@app.post("/session/{session_id}/datasets", response_model=VisualizationSessionSummary)
def session_add_dataset(session_id: str, body: AddDatasetRequest):
    try:
        session = add_dataset(session_id, body.dataset_id, body.source_key)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/session/{session_id}/datasets/{dataset_id}", response_model=VisualizationSessionSummary)
def session_delete_dataset(session_id: str, dataset_id: str):
    try:
        session = remove_dataset(session_id, dataset_id)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/session/{session_id}/pipeline", response_model=VisualizationSessionSummary)
def session_set_pipeline(session_id: str, body: PipelineUpdateRequest):
    try:
        validate_pipeline_steps(body.steps)
        session = set_pipeline(session_id, body.steps)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/session/{session_id}/buffer")
def session_get_buffer(session_id: str):
    try:
        return {"session_id": session_id, "commands": get_buffer(session_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/session/{session_id}/buffer/commands", response_model=VisualizationSessionSummary)
def session_push_buffer_command(session_id: str, body: BufferCommandRequest):
    try:
        validate_pipeline_steps([body.command])
        session = append_buffer_command(session_id, body.command)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/session/{session_id}/buffer/apply", response_model=VisualizationSessionSummary)
def session_apply_buffer(session_id: str, body: BufferApplyRequest | None = None):
    try:
        clear_after_apply = True if body is None else body.clear_after_apply
        session = apply_buffer_to_pipeline(session_id, clear_after_apply=clear_after_apply)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/session/{session_id}/buffer", response_model=VisualizationSessionSummary)
def session_clear_buffer(session_id: str):
    try:
        session = clear_buffer(session_id)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/session/{session_id}/charts")
def session_list_charts(session_id: str):
    try:
        session = get_session(session_id)
        return {"session_id": session_id, "charts": session.chart_definitions}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/session/{session_id}/charts", response_model=VisualizationSessionSummary)
def session_append_chart(session_id: str, body: ChartUpsertRequest):
    try:
        validate_chart_definition(body.chart)
        session = append_chart_definition(session_id, body.chart)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/session/{session_id}/charts", response_model=VisualizationSessionSummary)
def session_clear_charts_route(session_id: str):
    try:
        session = clear_charts(session_id)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/session/{session_id}/snapshots")
def session_list_snapshots(session_id: str):
    try:
        session = get_session(session_id)
        return {"session_id": session_id, "snapshots": session.saved_snapshots}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/session/{session_id}/snapshots", response_model=VisualizationSessionSummary)
def session_append_snapshot(session_id: str, body: SnapshotAppendRequest):
    try:
        validate_save_snapshot(body.snapshot)
        pipeline = SessionPipeline(session_id=session_id)
        bundle = pipeline.materialize_snapshot(body.snapshot)
        session = append_saved_snapshot(session_id, bundle)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/session/{session_id}/snapshots", response_model=VisualizationSessionSummary)
def session_clear_snapshots_route(session_id: str):
    try:
        session = clear_saved_snapshots(session_id)
        return _session_summary(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/session/{session_id}/buffer/preview")
def session_buffer_preview(
    session_id: str,
    county: str | None = None,
    city: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        commands = get_buffer(session_id)
        rows = fetch_session_observations(
            db=db,
            session_id=session_id,
            county=county,
            city=city,
            year_min=year_min,
            year_max=year_max,
            limit=limit,
            extra_steps=commands,
        )
        return {
            "session_id": session_id,
            "buffer_count": len(commands),
            "row_count": len(rows),
            "rows": rows,
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/session/{session_id}/datasets/{dataset_id}/verify", response_model=DatasetVerifyResult)
def session_verify_dataset(
    session_id: str,
    dataset_id: str,
    db: Session = Depends(get_db),
):
    try:
        info = verify_session_dataset(db, session_id, dataset_id)
        return DatasetVerifyResult.model_validate(info)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/session/{session_id}/preview")
def session_preview(
    session_id: str,
    county: str | None = None,
    city: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        rows = resolve_observation_rows(
            db=db,
            session_id=session_id,
            county=county,
            city=city,
            year_min=year_min,
            year_max=year_max,
            limit=limit,
        )
        return {"session_id": session_id, "row_count": len(rows), "rows": rows}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.get("/comparison/datasets")
def comparison_datasets(
    source_keys: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    city: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    db: Session = Depends(get_db),
):
    selected = [key.strip() for key in (source_keys or "").split(",") if key.strip()]
    if not selected and not session_id:
        raise HTTPException(
            status_code=400,
            detail="Provide comma-separated source_keys or session_id for merged dataset comparison.",
        )

    return compare_datasets(
        db=db,
        source_keys=selected if selected else None,
        session_id=session_id,
        county=county,
        city=city,
        year_min=year_min,
        year_max=year_max,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )

@app.get("/sources/{source_key}", response_model=SourceDefinition)
def source_detail(source_key: str):
    try:
        return get_source(source_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/ingest/{source_key}", response_model=IngestionResult)
def ingest(source_key: str, db: Session = Depends(get_db)):
    try:
        return ingest_source(db, source_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.get("/analysis/selected-correlation")
def analysis_selected_correlation(
    variables: str,
    source_key: str | None = None,
    session_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    db: Session = Depends(get_db),
):
    selected = [v.strip() for v in variables.split(",") if v.strip()]

    return selected_variable_correlation(
        db=db,
        variables=selected,
        source_key=source_key,
        session_id=session_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )



@app.get("/observations/summary")
def observations_summary(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT dataset_category, source_key, COUNT(*) AS count
        FROM regional_observations
        GROUP BY dataset_category, source_key
        ORDER BY dataset_category, source_key
    """)).mappings().all()

    return [dict(row) for row in rows]


@app.get("/regions")
def regions(db: Session = Depends(get_db)):
    return list_regions(db)


@app.get("/observations/query")
def observations_query(
    source_key: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    county: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    bbox: str | None = Query(default=None),
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    search: str | None = None,
    observed_at_min: str | None = None,
    observed_at_max: str | None = None,
    metric_value_min: float | None = None,
    metric_value_max: float | None = None,
    metric_names: str | None = None,
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    mn_list = [x.strip() for x in (metric_names or "").split(",") if x.strip()] or None

    if session_id:
        try:
            return resolve_observation_rows(
                db=db,
                session_id=session_id,
                category=category,
                county=county,
                city=city,
                state=state,
                year_min=year_min,
                year_max=year_max,
                bbox=bbox,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                search=search,
                observed_at_min=observed_at_min,
                observed_at_max=observed_at_max,
                metric_value_min=metric_value_min,
                metric_value_max=metric_value_max,
                metric_names=mn_list,
                limit=limit,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return query_observations(
        db=db,
        source_key=source_key,
        category=category,
        county=county,
        city=city,
        state=state,
        year_min=year_min,
        year_max=year_max,
        bbox=bbox,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        search=search,
        observed_at_min=observed_at_min,
        observed_at_max=observed_at_max,
        metric_value_min=metric_value_min,
        metric_value_max=metric_value_max,
        metric_names=mn_list,
        limit=limit,
    )

@app.get("/exports/observations.csv")
def observations_csv(
    source_key: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    county: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    bbox: str | None = None,
    search: str | None = None,
    observed_at_min: str | None = None,
    observed_at_max: str | None = None,
    metric_value_min: float | None = None,
    metric_value_max: float | None = None,
    metric_names: str | None = None,
    limit: int = Query(default=10000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    mn_list = [x.strip() for x in (metric_names or "").split(",") if x.strip()] or None

    if session_id:
        try:
            rows = resolve_observation_rows(
                db=db,
                session_id=session_id,
                category=category,
                county=county,
                city=city,
                state=state,
                year_min=year_min,
                year_max=year_max,
                bbox=bbox,
                search=search,
                observed_at_min=observed_at_min,
                observed_at_max=observed_at_max,
                metric_value_min=metric_value_min,
                metric_value_max=metric_value_max,
                metric_names=mn_list,
                limit=limit,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    else:
        rows = query_observations(
            db=db,
            source_key=source_key,
            category=category,
            county=county,
            city=city,
            state=state,
            year_min=year_min,
            year_max=year_max,
            bbox=bbox,
            search=search,
            observed_at_min=observed_at_min,
            observed_at_max=observed_at_max,
            metric_value_min=metric_value_min,
            metric_value_max=metric_value_max,
            metric_names=mn_list,
            limit=limit,
        )
    return rows_to_csv_response(rows)

@app.get("/trends/datasets")
def trends_datasets(
    source_key: str | None = None,
    session_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    db: Session = Depends(get_db),
):
    return dataset_trends(
        db=db,
        source_key=source_key,
        session_id=session_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )

@app.get("/analysis/correlation")
def analysis_correlation(
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    db: Session = Depends(get_db),
):
    return correlation_analysis(
        db=db,
        source_key=source_key,
        session_id=session_id,
        county=county,
        year_min=year_min,
        year_max=year_max,
    )


@app.get("/analysis/regression")
def analysis_regression(
    x: str = "year",
    y: str = "metric_value",
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    db: Session = Depends(get_db),
):
    return regression_analysis(
        db=db,
        source_key=source_key,
        session_id=session_id,
        county=county,
        year_min=year_min,
        year_max=year_max,
        x=x,
        y=y,
    )


@app.get("/analysis/county-compare")
def analysis_county_compare(
    source_key: str | None = None,
    session_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    db: Session = Depends(get_db),
):
    return county_compare_analysis(
        db=db,
        source_key=source_key,
        session_id=session_id,
        year_min=year_min,
        year_max=year_max,
    )


@app.get("/modeling/risk-surface")
def modeling_risk_surface(
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    resolution: int = Query(default=24, ge=4, le=128),
    db: Session = Depends(get_db),
):
    return risk_surface_model(
        db=db,
        source_key=source_key,
        session_id=session_id,
        county=county,
        year_min=year_min,
        year_max=year_max,
        resolution=resolution,
    )


@app.get("/modeling/spatial-interpolation")
def modeling_spatial_interpolation(
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    resolution: int = Query(default=24, ge=4, le=128),
    db: Session = Depends(get_db),
):
    return spatial_interpolation_model(
        db=db,
        source_key=source_key,
        session_id=session_id,
        county=county,
        year_min=year_min,
        year_max=year_max,
        resolution=resolution,
    )


@app.get("/modeling/matrix-compare")
def modeling_matrix_compare(
    source_key: str | None = None,
    session_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    db: Session = Depends(get_db),
):
    return matrix_compare_model(
        db=db,
        source_key=source_key,
        session_id=session_id,
        year_min=year_min,
        year_max=year_max,
    )


@app.get("/comparison/presets")
def comparison_presets_route():
    return comparison_presets()


@app.get("/comparison/sankey")
def comparison_sankey(
    source_key: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    db: Session = Depends(get_db),
):
    return build_sankey(
        db=db,
        source_key=source_key,
        session_id=session_id,
        category=category,
        county=county,
        year_min=year_min,
        year_max=year_max,
    )


@app.get("/comparison/cross-domain")
def comparison_cross_domain(
    source_key: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    db: Session = Depends(get_db),
):
    return cross_domain_compare(
        db=db,
        source_key=source_key,
        session_id=session_id,
        category=category,
        county=county,
        year_min=year_min,
        year_max=year_max,
    )
