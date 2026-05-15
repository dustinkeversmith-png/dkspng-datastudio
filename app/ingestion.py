from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.connectors.factory import create_connector
from app.models import IngestionRun, RegionalObservation
from app.normalization import normalize_dataframe
from app.schemas import IngestionResult
from app.source_registry import get_source


def ingest_source(db: Session, source_key: str) -> IngestionResult:
    source = get_source(source_key)
    run = IngestionRun(source_key=source_key, status="running")
    db.add(run)
    db.commit()

    try:
        connector = create_connector(source)
        df = connector.fetch()
        normalized = normalize_dataframe(source, df)

        written = 0
        for record in normalized:
            observation = RegionalObservation(**record)
            db.add(observation)
            db.flush()

            if record.get("latitude") is not None and record.get("longitude") is not None:
                db.execute(
                    text("""
                        UPDATE regional_observations
                        SET geometry = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                        WHERE id = :id
                    """),
                    {"lon": record["longitude"], "lat": record["latitude"], "id": observation.id},
                )

            written += 1

        run.status = "success"
        run.finished_at = datetime.now(timezone.utc)
        run.rows_read = len(df)
        run.rows_written = written
        db.commit()

        return IngestionResult(
            source_key=source_key,
            status="success",
            rows_read=len(df),
            rows_written=written,
        )

    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = str(exc)
        db.add(run)
        db.commit()

        return IngestionResult(
            source_key=source_key,
            status="failed",
            rows_read=0,
            rows_written=0,
            error_message=str(exc),
        )
