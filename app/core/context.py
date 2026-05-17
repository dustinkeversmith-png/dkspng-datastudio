from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from app.workflow.source_binding import Source

@dataclass
class ExecutionContext:
    source: Source
    source_key: Optional[str] = None
    mapping: Optional[Any] = None  # BaseMapping or string, using Any for now to avoid circular imports later
    metadata: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
