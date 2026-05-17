from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class ComponentResult:
    component_key: str
    result_type: str
    data: Any = None
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    lineage: Dict[str, Any] = field(default_factory=dict)
