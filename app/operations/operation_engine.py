from app.core.context import ExecutionContext
from app.core.result import ComponentResult
from app.operations.base_operation import BaseOperation

class OperationEngine:
    def execute(self, operation: BaseOperation, context: ExecutionContext) -> ComponentResult:
        val_result = operation.validate(context)
        if not val_result.ok:
            raise ValueError(f"Validation failed for operation '{operation.component_key}': {val_result.errors}")
        return operation.execute(context)
