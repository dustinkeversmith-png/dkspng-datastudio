from typing import Any, Dict, List, Optional
from app.workflow.source_binding import Source
import pandas as pd

def select_source_dataframe(source: Source, source_key: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Select data from the given Source object, safely interacting with existing Source.fetch().
    """
    kwargs = {}
    if source_key:
        kwargs["source_key"] = source_key
    if limit is not None:
        kwargs["limit"] = limit

    rows = source.fetch(**kwargs)
    return pd.DataFrame(rows)
