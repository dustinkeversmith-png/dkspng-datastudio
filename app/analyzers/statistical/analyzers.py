from typing import Any, Dict
import pandas as pd
from app.analyzers.base_analyzer import BaseAnalyzer
from app.core.context import ExecutionContext
from app.core.validation import ValidationResult
from app.core.result import ComponentResult
from app.core.lineage import create_lineage_record
from app.mappings.mapping_targets import ResolvedMapping

class CorrelationAnalyzer(BaseAnalyzer):
    def __init__(self, target_mapping: ResolvedMapping, method: str = "pearson"):
        self.target_mapping = target_mapping
        self.method = method

    @property
    def component_key(self) -> str:
        return "correlation_analyzer"

    @property
    def display_name(self) -> str:
        return "Correlation Analyzer"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        numeric_targets = self.target_mapping.by_type("numeric")
        if not numeric_targets and not self.target_mapping.by_role("numeric"):
             # If no explicitly typed numeric targets, we'll try to calculate it anyway on all columns in execute
             pass
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        from app.core.selectors import select_source_dataframe
        df = select_source_dataframe(context.source, context.source_key)
        
        numeric_cols = []
        # Find numeric fields via mapping or fallback to auto-detection
        for t in self.target_mapping.by_role("numeric"):
            name = t.selector.get("name")
            if name in df.columns:
                numeric_cols.append(name)
                
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if len(numeric_cols) < 2:
            return ComponentResult(
                component_key=self.component_key,
                result_type="metrics",
                data={"error": "Not enough numeric columns for correlation."}
            )
            
        corr_matrix = df[numeric_cols].corr(method=self.method)
        
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, {"method": self.method})
        return ComponentResult(
            component_key=self.component_key,
            result_type="metrics",
            data=corr_matrix.to_dict(),
            lineage=lineage
        )

class DistributionAnalyzer(BaseAnalyzer):
    def __init__(self, target_mapping: ResolvedMapping):
        self.target_mapping = target_mapping

    @property
    def component_key(self) -> str:
        return "distribution_analyzer"

    @property
    def display_name(self) -> str:
        return "Distribution Analyzer"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        from app.core.selectors import select_source_dataframe
        df = select_source_dataframe(context.source, context.source_key)
        
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        
        stats = {}
        for col in numeric_cols:
            stats[col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "q25": float(df[col].quantile(0.25)),
                "q75": float(df[col].quantile(0.75))
            }
            
        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, {})
        return ComponentResult(
            component_key=self.component_key,
            result_type="metrics",
            data=stats,
            lineage=lineage
        )
