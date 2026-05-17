from typing import Any, Dict

def create_lineage_record(parent_source_key: str, operation_key: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new lineage record."""
    from datetime import datetime
    import uuid
    return {
        "record_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "parent_source_key": parent_source_key,
        "operation_key": operation_key,
        "params": params
    }

def append_lineage(existing: Dict[str, Any], new_record: Dict[str, Any]) -> Dict[str, Any]:
    """Append a new record to an existing lineage tracking dictionary."""
    history = existing.get("history", [])
    return {
        "history": history + [new_record]
    }
