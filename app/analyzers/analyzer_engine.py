from app.core.context import ExecutionContext
from app.core.result import ComponentResult
from app.analyzers.base_analyzer import BaseAnalyzer

class AnalyzerEngine:
    def execute(self, analyzer: BaseAnalyzer, context: ExecutionContext) -> ComponentResult:
        val_result = analyzer.validate(context)
        if not val_result.ok:
            raise ValueError(f"Validation failed for analyzer '{analyzer.component_key}': {val_result.errors}")
        return analyzer.execute(context)
