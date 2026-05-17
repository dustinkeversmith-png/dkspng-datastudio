from typing import List
from app.operations.base_operation import BaseOperation
from app.core.context import ExecutionContext
from app.core.validation import ValidationResult
from app.core.result import ComponentResult
from app.core.lineage import create_lineage_record

class OperationPipeline(BaseOperation):
    def __init__(self, pipeline_key: str, operations: List[BaseOperation]):
        self.pipeline_key = pipeline_key
        self.operations = operations

    @property
    def component_key(self) -> str:
        return self.pipeline_key

    @property
    def display_name(self) -> str:
        return f"Pipeline: {self.pipeline_key}"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        errors = []
        for op in self.operations:
            res = op.validate(context)
            if not res.ok:
                errors.extend(res.errors)
        if errors:
            return ValidationResult.failure(errors)
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        # In a real system, the dataframe would be passed through operations.
        # But since our operations currently fetch from context.source, 
        # passing intermediate results requires a modified context or Source.
        # For Phase 3, we execute sequentially, passing the modified df forward
        # by creating temporary contexts/sources or just having operations accept df via context.params
        
        from app.core.selectors import select_source_dataframe
        df = select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        
        lineage_history = []
        
        for op in self.operations:
            # We override the dataframe natively so ops can use it.
            # We inject the current df into params for operations to pick up if they are pipeline-aware.
            # To avoid refactoring all atomic operations, we temporarily mock select_source_dataframe
            # Actually, standard pipelines should wrap the data into a DerivedSource, but for now we'll 
            # execute them by injecting into context.params['df']. 
            
            # Since atomic ops use `select_source_dataframe(context.source)`, we will need to
            # make atomic ops check `context.params.get("df")` first.
            
            context.params["df"] = df
            result = op.execute(context)
            df = result.data
            lineage_history.append(result.lineage)
            
        final_lineage = create_lineage_record(context.source_key or "unknown", self.component_key, {"operations": len(self.operations)})
        final_lineage["history"] = lineage_history

        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=final_lineage
        )
