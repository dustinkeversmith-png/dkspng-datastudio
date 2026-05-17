from app.core.context import ExecutionContext
from app.core.result import ComponentResult
from app.views.base_view import BaseView

class ViewEngine:
    def render(self, view: BaseView, context: ExecutionContext) -> ComponentResult:
        val_result = view.validate(context)
        if not val_result.ok:
            raise ValueError(f"Validation failed for view '{view.component_key}': {val_result.errors}")
        return view.execute(context)
