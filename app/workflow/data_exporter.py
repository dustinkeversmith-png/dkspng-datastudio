import csv
import json
from pathlib import Path
from typing import Any

from app.workflow.source_binding import Source


class DataExporter:
    """Component to export fetched data to disk (CSV or JSON)."""

    def to_csv(self, source: Source, filename: str, rows: list[dict[str, Any]] | None = None, **kwargs) -> str:
        """Export source data to a CSV file."""
        data = rows if rows is not None else source.fetch(**kwargs)
        if not data:
            print(f"Warning: No data to export for source '{source.key}'.")
            return ""

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"Exported {len(data)} rows to {path.resolve()}")
        return str(path)

    def to_json(self, source: Source, filename: str, rows: list[dict[str, Any]] | None = None, **kwargs) -> str:
        """Export source data to a JSON file."""
        data = rows if rows is not None else source.fetch(**kwargs)
        if not data:
            print(f"Warning: No data to export for source '{source.key}'.")
            return ""

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"Exported {len(data)} rows to {path.resolve()}")
        return str(path)


def data_exporter() -> DataExporter:
    """Create a standalone data exporter."""
    return DataExporter()
