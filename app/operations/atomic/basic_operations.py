from typing import Any, Dict, List, Optional
from app.operations.base_operation import BaseOperation
from app.core.context import ExecutionContext
from app.core.validation import ValidationResult
from app.core.result import ComponentResult
from app.core.selectors import select_source_dataframe
from app.core.lineage import create_lineage_record
import pandas as pd

class SelectOperation(BaseOperation):
    def __init__(self, target: Dict[str, Any]):
        self.target = target

    @property
    def component_key(self) -> str:
        return "select_operation"

    @property
    def display_name(self) -> str:
        return "Select Target"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if "target_type" not in self.target:
            return ValidationResult.failure(["Target must specify target_type."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        if "df" in context.params:
            df = context.params["df"]
        else:
            df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        
        target_type = self.target.get("target_type")
        if target_type == "field":
            names = self.target.get("names", [])
            # Only select if fields exist
            valid_names = [n for n in names if n in df.columns]
            df = df[valid_names] if valid_names else df
        
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, self.target)
        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=lineage
        )

class FilterOperation(BaseOperation):
    def __init__(self, target: Dict[str, Any]):
        self.target = target

    @property
    def component_key(self) -> str:
        return "filter_operation"

    @property
    def display_name(self) -> str:
        return "Filter Target"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if "where" not in self.target:
            return ValidationResult.failure(["Filter operation requires a 'where' clause in target."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        where = self.target["where"]
        
        field = where.get("field")
        op = where.get("op")
        value = where.get("value")
        
        if field in df.columns:
            if op == ">":
                df = df[df[field] > value]
            elif op == "<":
                df = df[df[field] < value]
            elif op == "==":
                df = df[df[field] == value]
            elif op == ">=":
                df = df[df[field] >= value]
            elif op == "<=":
                df = df[df[field] <= value]
                
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, self.target)
        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=lineage
        )

class RenameOperation(BaseOperation):
    def __init__(self, target: Dict[str, Any]):
        self.target = target

    @property
    def component_key(self) -> str:
        return "rename_operation"

    @property
    def display_name(self) -> str:
        return "Rename Fields"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if "mapping" not in self.target:
            return ValidationResult.failure(["Rename operation requires a 'mapping' dict in target."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        mapping = self.target["mapping"]
        
        df = df.rename(columns=mapping)
                
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, self.target)
        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=lineage
        )

class RemoveOperation(BaseOperation):
    def __init__(self, target: Dict[str, Any]):
        self.target = target

    @property
    def component_key(self) -> str:
        return "remove_operation"

    @property
    def display_name(self) -> str:
        return "Remove Target"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if "target_type" not in self.target:
            return ValidationResult.failure(["Remove operation requires 'target_type'."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        target_type = self.target.get("target_type")
        
        if target_type == "field":
            names = self.target.get("names", [])
            valid_names = [n for n in names if n in df.columns]
            df = df.drop(columns=valid_names)
        elif target_type == "record":
            where = self.target.get("where", {})
            field = where.get("field")
            op = where.get("op")
            value = where.get("value")
            
            if field in df.columns:
                if op == ">":
                    df = df[~(df[field] > value)]
                elif op == "<":
                    df = df[~(df[field] < value)]
                elif op == "==":
                    df = df[~(df[field] == value)]
                elif op == "<=":
                    df = df[~(df[field] <= value)]
                elif op == ">=":
                    df = df[~(df[field] >= value)]
                
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, self.target)
        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=lineage
        )

class ExpressionOperation(BaseOperation):
    def __init__(self, target_type: str, output_target: str, expression: str):
        self.target_type = target_type
        self.output_target = output_target
        self.expression = expression

    @property
    def component_key(self) -> str:
        return "expression_operation"

    @property
    def display_name(self) -> str:
        return "Expression Derivation"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if not self.expression:
            return ValidationResult.failure(["Expression cannot be empty."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        
        try:
            # Safely evaluate using pandas built-in eval engine which parses a restricted expression grammar
            df[self.output_target] = df.eval(self.expression)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression '{self.expression}': {e}")
                
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, {"expression": self.expression})
        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=lineage
        )

class NormalizeOperation(BaseOperation):
    def __init__(self, target: Dict[str, Any]):
        self.target = target

    @property
    def component_key(self) -> str:
        return "normalize_operation"

    @property
    def display_name(self) -> str:
        return "Normalize Numeric Fields"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if "field" not in self.target:
            return ValidationResult.failure(["Normalize operation requires 'field'."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        field = self.target["field"]
        method = self.target.get("method", "minmax")
        
        if field in df.columns:
            col_data = df[field]
            if method == "minmax":
                min_val = col_data.min()
                max_val = col_data.max()
                if max_val > min_val:
                    df[field] = (col_data - min_val) / (max_val - min_val)
                else:
                    df[field] = 0
                
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, self.target)
        return ComponentResult(
            component_key=self.component_key,
            result_type="dataframe",
            data=df,
            lineage=lineage
        )
