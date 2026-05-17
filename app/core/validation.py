from dataclasses import dataclass, field
from typing import List

@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(ok=True)

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        return cls(ok=False, errors=errors)
