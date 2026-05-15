"""Named façade for reshape-oriented buffer commands (stack/melt, renames)."""

from __future__ import annotations

from app.workflow.session_pipeline import SessionPipeline


class DataReshaper:
    """Use with an existing :class:`SessionPipeline` to keep reshape intent explicit."""

    def __init__(self, pipeline: SessionPipeline) -> None:
        self._pipeline = pipeline

    def melt(
        self,
        id_vars: list[str],
        measure_vars: list[str],
        *,
        var_name: str = "variable",
        value_name: str = "value",
        dataset_id: str | None = None,
    ) -> SessionPipeline:
        """Wide → long (same as ``SessionPipeline.stack_columns``)."""
        return self._pipeline.stack_columns(
            id_vars,
            measure_vars,
            var_name=var_name,
            value_name=value_name,
            dataset_id=dataset_id,
        )

    def rename(self, mapping: dict[str, str], dataset_id: str | None = None) -> SessionPipeline:
        return self._pipeline.rename_columns(mapping, dataset_id=dataset_id)
