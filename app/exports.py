import csv
from io import StringIO

from fastapi.responses import StreamingResponse


def rows_to_csv_response(rows: list[dict], filename: str = "regional_observations.csv"):
    buffer = StringIO()

    if rows:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
