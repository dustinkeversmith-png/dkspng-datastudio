import json
import sys
from typing import Optional

import typer
import requests
from rich import print
from rich.table import Table

from app.db import SessionLocal
from app.ingestion import ingest_source
from app.source_registry import list_sources
from app.session_query import verify_session_dataset
from app.visualization_session import add_dataset, create_session, get_session

cli = typer.Typer()
session_cli = typer.Typer(help="Visualization session: combine registered sources with optional pipeline")
cli.add_typer(session_cli, name="session")

DEFAULT_API = "http://127.0.0.1:8000"


def _api_base() -> str:
    return DEFAULT_API


@cli.command()
def sources():
    for source in list_sources():
        print(f"[bold]{source.source_key}[/bold] — {source.display_name} ({source.connector_type})")


@cli.command()
def ingest(source: str):
    db = SessionLocal()
    try:
        result = ingest_source(db, source)
        print(result.model_dump())
    finally:
        db.close()


@session_cli.command("create")
def session_create(
    label: Optional[str] = typer.Option(None, "--label", "-l", help="Optional session label"),
):
    """Create a visualization session (in-memory on the API server)."""
    body = {"label": label} if label else {}
    r = requests.post(f"{_api_base()}/session", json=body, timeout=30.0)
    if r.status_code >= 400:
        print(f"[red]{r.status_code}[/red] {r.text}")
        sys.exit(1)
    data = r.json()
    print("[bold]session_id[/bold]", data["session_id"])
    print(json.dumps(data, indent=2))


@session_cli.command("add-dataset")
def session_add_dataset(
    session_id: str = typer.Argument(..., help="UUID from session create"),
    dataset_id: str = typer.Option(..., "--id", "-i", help="Stable dataset id within the session (e.g. fires_a)"),
    source_key: str = typer.Option(..., "--source", "-s", help="Registered source_key from `sources`"),
):
    """Attach a registry source to a session under your chosen dataset id."""
    payload = {"dataset_id": dataset_id, "source_key": source_key}
    r = requests.post(f"{_api_base()}/session/{session_id}/datasets", json=payload, timeout=30.0)
    if r.status_code >= 400:
        print(f"[red]{r.status_code}[/red] {r.text}")
        sys.exit(1)
    print(json.dumps(r.json(), indent=2))


@session_cli.command("verify")
def session_verify(
    session_id: str = typer.Argument(...),
    dataset_id: str = typer.Option(..., "--id", "-i"),
):
    """Summarize columns and sample rows for one dataset binding (direct DB read)."""
    db = SessionLocal()
    try:
        info = verify_session_dataset(db, session_id, dataset_id)
    except KeyError as exc:
        print(f"[red]{exc}[/red]")
        sys.exit(1)
    finally:
        db.close()

    table = Table(title=f"Dataset {dataset_id} ({info['source_key']})")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("row_count", str(info["row_count"]))
    table.add_row("truncated", str(info["truncated"]))
    table.add_row("columns", ", ".join(info["columns"][:40]) + ("…" if len(info["columns"]) > 40 else ""))
    print(table)
    print("[bold]sample_rows[/bold]")
    print(json.dumps(info["sample_rows"], indent=2, default=str))


@session_cli.command("preview")
def session_preview_api(
    session_id: str = typer.Argument(...),
    limit: int = typer.Option(20, "--limit", "-n"),
):
    """Preview merged session rows after pipeline (calls GET /session/{id}/preview)."""
    r = requests.get(
        f"{_api_base()}/session/{session_id}/preview",
        params={"limit": limit},
        timeout=60.0,
    )
    if r.status_code >= 400:
        print(f"[red]{r.status_code}[/red] {r.text}")
        sys.exit(1)
    print(json.dumps(r.json(), indent=2, default=str))


@session_cli.command("show")
def session_show_local(session_id: str = typer.Argument(...)):
    """Show session state from the in-process store (only works in the same Python process as the server)."""
    try:
        s = get_session(session_id)
    except KeyError as exc:
        print(f"[red]{exc}[/red]")
        sys.exit(1)
    print("session_id:", s.session_id)
    print("label:", s.label)
    print("datasets:", json.dumps({k: v.source_key for k, v in s.datasets.items()}, indent=2))
    print("pipeline steps:", len(s.pipeline))


@session_cli.command("add-dataset-local")
def session_add_local(
    session_id: str = typer.Argument(...),
    dataset_id: str = typer.Option(..., "--id", "-i"),
    source_key: str = typer.Option(..., "--source", "-s"),
):
    """Add a dataset using the in-process store (dev only; use add-dataset against a running API)."""
    try:
        s = add_dataset(session_id, dataset_id, source_key)
    except (KeyError, ValueError) as exc:
        print(f"[red]{exc}[/red]")
        sys.exit(1)
    print(json.dumps({"session_id": s.session_id, "datasets": {k: v.source_key for k, v in s.datasets.items()}}, indent=2))


@session_cli.command("create-local")
def session_create_local(label: Optional[str] = typer.Option(None, "--label", "-l")):
    """Create a session in the in-process store (for tests / same-process tools)."""
    s = create_session(label=label)
    print(s.session_id)


if __name__ == "__main__":
    cli()
