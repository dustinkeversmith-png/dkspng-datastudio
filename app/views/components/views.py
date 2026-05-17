from typing import Any, Dict, List
from app.views.base_view import BaseView
from app.core.context import ExecutionContext
from app.core.validation import ValidationResult
from app.core.result import ComponentResult
from app.core.selectors import select_source_dataframe

class TableView(BaseView):
    def __init__(self, target_mapping=None):
        self.target_mapping = target_mapping

    @property
    def component_key(self) -> str:
        return "table_view"

    @property
    def display_name(self) -> str:
        return "Table View"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit", 100))
        
        # If mapping is provided, only include those fields and alias them
        if self.target_mapping:
            headers = []
            columns_to_keep = []
            for target in self.target_mapping.by_type("field"):
                col_name = target.selector.get("name")
                if col_name in df.columns:
                    columns_to_keep.append(col_name)
                    headers.append(target.display_name or col_name)
            
            if columns_to_keep:
                df = df[columns_to_keep]
                df.columns = headers
            else:
                headers = list(df.columns)
        else:
            headers = list(df.columns)
            
        rows = df.to_dict(orient="records")
        
        data = {
            "type": "table",
            "headers": headers,
            "rows": rows
        }
        
        return ComponentResult(
            component_key=self.component_key,
            result_type="view_structure",
            data=data
        )

class SummaryView(BaseView):
    @property
    def component_key(self) -> str:
        return "summary_view"

    @property
    def display_name(self) -> str:
        return "Summary View"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))
        
        data = {
            "type": "summary",
            "total_records": len(df),
            "columns": list(df.columns),
            "numeric_summaries": {}
        }
        
        numeric_df = df.select_dtypes(include="number")
        for col in numeric_df.columns:
            data["numeric_summaries"][col] = {
                "min": float(numeric_df[col].min()),
                "max": float(numeric_df[col].max()),
                "mean": float(numeric_df[col].mean())
            }
            
        return ComponentResult(
            component_key=self.component_key,
            result_type="view_structure",
            data=data
        )

class CardView(BaseView):
    def __init__(self, target_mapping):
        self.target_mapping = target_mapping

    @property
    def component_key(self) -> str:
        return "card_view"

    @property
    def display_name(self) -> str:
        return "Card View"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        if not self.target_mapping:
             return ValidationResult.failure(["CardView requires a target_mapping to assign title/description roles."])
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        df = select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit", 100))
        
        title_targets = self.target_mapping.by_role("title")
        desc_targets = self.target_mapping.by_role("description")
        
        title_col = title_targets[0].selector.get("name") if title_targets else df.columns[0]
        desc_col = desc_targets[0].selector.get("name") if desc_targets and len(df.columns) > 1 else df.columns[1] if len(df.columns) > 1 else None
        
        cards = []
        for _, row in df.iterrows():
            cards.append({
                "title": str(row.get(title_col, "")),
                "description": str(row.get(desc_col, "")) if desc_col else "",
                "raw_data": row.to_dict()
            })
            
        data = {
            "type": "cards",
            "cards": cards
        }
        
        return ComponentResult(
            component_key=self.component_key,
            result_type="view_structure",
            data=data
        )
