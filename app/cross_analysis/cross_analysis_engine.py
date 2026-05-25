"""
CrossAnalysisEngine — runs models across all variable-group pairs on a
fused multi-source DataFrame.
"""
from __future__ import annotations
from typing import Any
import pandas as pd

from app.cross_analysis.cross_analysis_spec import CrossAnalysisSpec
from app.cross_analysis.cross_analysis_result import CrossAnalysisResult
from app.models.model_engine import ModelEngine
from app.models.model_result import ModelResult


class CrossAnalysisEngine:
    """Orchestrate cross-source model runs per the spec."""

    def __init__(
        self,
        combined_df: pd.DataFrame,
        source_key: str = "combined",
        plot_dir: str = "data/plots/project2",
    ) -> None:
        self.df = combined_df.copy()
        self.source_key = source_key
        self.plot_dir = plot_dir

    def run(self, spec: CrossAnalysisSpec) -> CrossAnalysisResult:
        results: list[ModelResult] = []
        engine = ModelEngine(self.df, self.source_key)
        pairs = spec.all_pairs()

        print(f"  [CrossAnalysis] {len(pairs)} feature→target pairs × {len(spec.models)} models")

        for feat_group, tgt_group in pairs:
            feat_cols = [c for c in spec.variable_groups.get(feat_group, []) if c in self.df.columns]
            tgt_cols = [c for c in spec.variable_groups.get(tgt_group, []) if c in self.df.columns]

            if not feat_cols or not tgt_cols:
                continue

            # Cap features
            feat_cols = feat_cols[:spec.max_features]
            # Use first available target column
            target_col = self._pick_target(tgt_cols)

            for model_key in spec.models:
                label = f"{feat_group}→{tgt_group}"
                try:
                    result = engine.run(
                        model_key=model_key,
                        features=feat_cols,
                        target=target_col,
                        plot=True,
                        extra_context={
                            "plot_dir": self.plot_dir,
                            "pair_label": label,
                        },
                    )
                    result.metadata["pair"] = label
                    result.metadata["feature_group"] = feat_group
                    result.metadata["target_group"] = tgt_group
                    results.append(result)
                    status = "ok" if not result.metadata.get("error") and not result.metadata.get("warning") else "warn"
                    print(f"    [{status}] {model_key} | {label} | target={target_col}")
                except Exception as e:
                    print(f"    [err] {model_key} | {label}: {e}")

        summary = self._summarise(results)
        return CrossAnalysisResult(
            spec_grouping=spec.grouping,
            model_results=results,
            summary=summary,
            lineage={"pairs": [f"{a}→{b}" for a, b in pairs], "models": spec.models},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pick_target(self, tgt_cols: list[str]) -> str | None:
        """Prefer numeric columns, otherwise fall back to first available."""
        for col in tgt_cols:
            if pd.api.types.is_numeric_dtype(self.df[col].dropna()):
                return col
        return tgt_cols[0] if tgt_cols else None

    @staticmethod
    def _summarise(results: list[ModelResult]) -> dict[str, Any]:
        ok = [r for r in results if not r.metadata.get("error") and not r.metadata.get("warning")]
        model_counts: dict[str, int] = {}
        for r in results:
            model_counts[r.model_key] = model_counts.get(r.model_key, 0) + 1
        return {
            "total_runs": len(results),
            "successful_runs": len(ok),
            "model_counts": model_counts,
        }
