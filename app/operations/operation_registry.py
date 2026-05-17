from typing import Dict, List
from app.operations.base_operation import BaseOperation

class OperationRegistry:
    def __init__(self):
        self._operations: Dict[str, BaseOperation] = {}

    def register(self, operation: BaseOperation, allow_duplicate: bool = False) -> None:
        key = operation.component_key
        if key in self._operations and not allow_duplicate:
            raise ValueError(f"Operation with key '{key}' is already registered.")
        self._operations[key] = operation

    def get(self, key: str) -> BaseOperation:
        if key not in self._operations:
            raise KeyError(f"Operation with key '{key}' not found in registry.")
        return self._operations[key]

    def has(self, key: str) -> bool:
        return key in self._operations

    def list_keys(self) -> List[str]:
        return list(self._operations.keys())
