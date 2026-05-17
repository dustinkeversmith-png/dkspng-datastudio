from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class MappingTarget:
    target_key: str
    target_type: str
    selector: Dict[str, Any]
    role: Optional[str] = None
    semantic_type: Optional[str] = None
    display_name: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedMapping:
    mapping_key: str
    targets: Dict[str, MappingTarget]
    source_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def by_role(self, role: str) -> List[MappingTarget]:
        return [t for t in self.targets.values() if t.role == role]

    def by_type(self, target_type: str) -> List[MappingTarget]:
        return [t for t in self.targets.values() if t.target_type == target_type]

    def get(self, target_key: str) -> MappingTarget:
        if target_key not in self.targets:
            raise KeyError(f"Mapping target '{target_key}' not found.")
        return self.targets[target_key]
