"""Source — the central stateful data container for Regional Data Studio.

API surface
-----------
Constructors / loading
    source(key_or_def)              factory function
    Source(key_or_def)              class constructor
    s.add_source(key_or_def)        add a sub-source (chained)
    s.add_dataframe(key, df)        attach a raw DataFrame

Subsetting / indexing
    s.subset(selections)            select columns per sub-source → new Source
    s.index(**queries)              DSL row+col slicing → new Source
    s.copy()                        deep-copy (alias for clone())
    s.clone()                       deep-copy

Column access (AxisExpr DSL)
    s["fire"]                       → SourceProxy
    s["fire"]["col"]                → AxisExpr

Mapping
    s.set_map(name, from_loc, to_loc, func)   register a named mapping
    s.map(name, index)              execute mapping → Column
    s.append(column, target_set)    append Column into a sub-source

Column IDs / names
    s.colids(source_key)            {0: col_name, ...}
    s.names(sources_set)            {src: {0: col_name}} for each src

Semantic roles
    s.name(source_key, {col: role}) attach semantic labels to columns

Discovery
    s.find_matching_types(srcs, types)
    s.find_matching_units(srcs)

Mutation
    s.add(target, expr_or_column)   add a computed column (replace mutate)
    s.remove(target)                remove column / rows / sub-source
    s.if_(condition)                → ConditionalMutator

Metadata
    s.generate_metadata()

Analysis (return typed result objects)
    s.log_regression(source_key, features, target)   → RegressionResult
    s.knn(source_key, features, target, k)           → KNNResult

Visualisation (return Chart objects)
    s.bar(x_expr, y_expr)           → Chart
    s.scatter(x_expr, y_expr)       → Chart
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

import pandas as pd

from app.schemas import SourceDefinition
from app.source_registry import get_source


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

class Source:

    def __init__(self, key_or_def: str | SourceDefinition | None = None):
        self.source_definitions: Dict[str, SourceDefinition] = {}
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Any] = {}
        self.mappings: Dict[str, Any] = {}
        self._named_roles: Dict[str, Dict[str, str]] = {}   # source → {col: role}
        self._registered_maps: Dict[str, dict] = {}          # name → map spec
        self.key: str | None = None

        if key_or_def:
            if isinstance(key_or_def, str):
                self.key = key_or_def
            else:
                self.key = key_or_def.source_key
            self.add_source(key_or_def)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def add_source(self, key_or_def: str | SourceDefinition) -> "Source":
        from app.connectors.factory import create_connector
        if isinstance(key_or_def, str):
            definition = get_source(key_or_def)
            key = key_or_def
        else:
            definition = key_or_def
            key = definition.source_key
        self.source_definitions[key] = definition
        connector = create_connector(definition)
        self.dataframes[key] = connector.fetch()
        return self

    def add_dataframe(self, key: str, df: pd.DataFrame) -> "Source":
        self.dataframes[key] = df
        return self

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def generate_metadata(self) -> "Source":
        from app.metadata_analyzer.analyzer import MetadataAnalyzer
        for key, definition in self.source_definitions.items():
            if key not in self.dataframes:
                continue
            patch = self.dataframes[key].head(100).to_dict(orient="records")
            analyzer = MetadataAnalyzer(source_key=key, source_url=definition.source_url)
            self.metadata[key] = analyzer.generate_profile(patch).model_dump()
        return self

    # ------------------------------------------------------------------
    # AxisExpr / SourceProxy access:  s["fire"]["col"]
    # ------------------------------------------------------------------

    def __getitem__(self, source_key: str) -> "SourceProxy":
        from app.expressions.axis_expr import SourceProxy
        return SourceProxy(self, source_key)

    # ------------------------------------------------------------------
    # Subsetting / indexing
    # ------------------------------------------------------------------

    def subset(self, selections: Dict[str, List[str]], inplace: bool = False) -> "Source":
        """Select named columns per sub-source → new Source (or mutate inplace)."""
        target = self if inplace else self._empty_clone()
        for s_key, cols in selections.items():
            if s_key in self.dataframes:
                available = [c for c in cols if c in self.dataframes[s_key].columns]
                target.dataframes[s_key] = self.dataframes[s_key][available].copy()
        return target

    def index(self, **queries) -> "Source":
        """DSL-aware row+col slicing.

        Each kwarg value is a 2-tuple: (row_expr, col_expr).
        Both may be:
          - a Python slice   → used directly with .iloc
          - a string         → parsed by IndexParser
          - a list           → used directly
        """
        from app.indexing.index_parser import parse_row_index, parse_col_index

        target = self.clone()
        for s_key, (row_expr, col_expr) in queries.items():
            if s_key not in target.dataframes:
                continue
            df = target.dataframes[s_key]

            row_idx = parse_row_index(row_expr)
            col_names = parse_col_index(col_expr, df)

            # Apply row slice
            if isinstance(row_idx, slice):
                df = df.iloc[row_idx]
            elif isinstance(row_idx, list):
                df = df.iloc[row_idx]

            # Apply column filter
            available = [c for c in col_names if c in df.columns]
            if available:
                df = df[available]

            target.dataframes[s_key] = df.reset_index(drop=True)

        return target

    def copy(self) -> "Source":
        """Return a deep copy of this Source (alias for clone())."""
        return self.clone()

    def clone(self) -> "Source":
        new_s = Source()
        new_s.key = f"{self.key}_clone"
        new_s.source_definitions = dict(self.source_definitions)
        new_s.metadata = dict(self.metadata)
        new_s.mappings = dict(self.mappings)
        new_s._named_roles = {k: dict(v) for k, v in self._named_roles.items()}
        new_s._registered_maps = dict(self._registered_maps)
        for k, v in self.dataframes.items():
            new_s.dataframes[k] = v.copy()
        return new_s

    # ------------------------------------------------------------------
    # Column IDs and names
    # ------------------------------------------------------------------

    def colids(self, source_key: str) -> Dict[int, str]:
        """Return {integer_index: column_name} for a sub-source."""
        if source_key not in self.dataframes:
            return {}
        return {i: col for i, col in enumerate(self.dataframes[source_key].columns)}

    def names(self, sources: Set[str]) -> Dict[str, Dict[int, str]]:
        """Return colids() for each source in the set."""
        return {s: self.colids(s) for s in sources if s in self.dataframes}

    # ------------------------------------------------------------------
    # Semantic naming
    # ------------------------------------------------------------------

    def name(self, source_key: str, column_mapping: Dict[str, str]) -> "Source":
        """Rename columns OR attach semantic roles.

        If the value is a new column name (different from current), rename it.
        Otherwise register as a semantic role tag.
        """
        if source_key not in self._named_roles:
            self._named_roles[source_key] = {}

        if source_key in self.dataframes:
            df = self.dataframes[source_key]
            rename_map: Dict[str, str] = {}
            for old_col, new_label in column_mapping.items():
                if old_col in df.columns and new_label not in df.columns:
                    rename_map[old_col] = new_label
                else:
                    self._named_roles[source_key][old_col] = new_label

            if rename_map:
                self.dataframes[source_key] = df.rename(columns=rename_map)

        return self

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    def set_map(
        self,
        name: str,
        from_loc: tuple[str, int | str],
        to_loc: tuple[str, int | str],
        func: Any = None,
    ) -> "Source":
        """Register a named mapping between two sub-source columns."""
        self._registered_maps[name] = {
            "from_loc": from_loc,
            "to_loc": to_loc,
            "func": func,
        }
        return self

    def map(self, name: str, index: str | int = "all") -> "Column":
        """Execute a registered mapping and return a Column object.

        Parameters
        ----------
        name:   name of mapping registered via set_map()
        index:  row selection expression (forwarded to IndexParser), or "all"
        """
        from app.mappings.column import Column
        from app.indexing.index_parser import parse_row_index

        if name not in self._registered_maps:
            raise KeyError(f"No mapping registered with name '{name}'")

        spec = self._registered_maps[name]
        src_key, src_col = spec["from_loc"]

        if src_key not in self.dataframes:
            raise KeyError(f"Source '{src_key}' not found in dataframes")

        df = self.dataframes[src_key]

        # Resolve column
        if isinstance(src_col, int):
            src_col = df.columns[src_col]

        series = df[src_col].copy()

        # Apply row selection
        if index != "all":
            row_idx = parse_row_index(str(index))
            if isinstance(row_idx, slice):
                series = series.iloc[row_idx]
            elif isinstance(row_idx, list):
                series = series.iloc[row_idx]

        # Apply transform function
        if spec["func"] is not None:
            series = series.apply(spec["func"])

        return Column(name=src_col, data=series, source_key=src_key, mapping_name=name)

    def append(self, column: "Column", target: Set[str] | tuple) -> "Source":
        """Append a Column object into a sub-source.

        target can be:
          - a set  {"fire", "metric_conversion"}  → first element = source key,
                                                     second = new col name
          - a tuple ("fire", "metric_conversion")
        """
        from app.mappings.column import Column as ColType

        if not isinstance(column, ColType):
            raise TypeError(f"Expected a Column object, got {type(column)}")

        target_list = list(target)
        dst_key = target_list[0]
        new_col_name = target_list[1] if len(target_list) > 1 else column.name

        if dst_key not in self.dataframes:
            raise KeyError(f"Target source '{dst_key}' not found")

        df = self.dataframes[dst_key]
        data = column.data.reset_index(drop=True)

        # Align lengths
        if len(data) > len(df):
            data = data.iloc[: len(df)]
        elif len(data) < len(df):
            import numpy as np
            pad = pd.Series([np.nan] * (len(df) - len(data)))
            data = pd.concat([data, pad], ignore_index=True)

        data.index = df.index
        df[new_col_name] = data
        return self

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def find_matching_types(self, sources: Set[str], types: Set[str]) -> Dict[str, List[str]]:
        """Return columns matching the given base types across sources."""
        from app.operations.data_ops import check_base_types
        matches: Dict[str, List[str]] = {}
        for s in sources:
            if s in self.dataframes:
                inferred = check_base_types(self, s)
                matches[s] = [col for col, t in inferred.items() if t in types]
        return matches

    def find_matching_units(self, sources: Set[str]) -> Dict[str, Any]:
        """Find columns with matching names (proxy for shared units) across sources.

        Returns a dict containing:
          - 'matching_unit_columns': list of column names present in ALL listed sources
          - 'cross_index': {col: [(src, idx), ...]} — cross-source indexing tuples
        """
        common_cols: set[str] | None = None
        for s in sources:
            if s in self.dataframes:
                col_set = set(self.dataframes[s].columns)
                common_cols = col_set if common_cols is None else common_cols & col_set

        if not common_cols:
            return {"matching_unit_columns": [], "cross_index": {}}

        cross_index: Dict[str, list] = {}
        for col in common_cols:
            cross_index[col] = []
            for s in sources:
                if s in self.dataframes and col in self.dataframes[s].columns:
                    idx = list(self.dataframes[s].columns).index(col)
                    cross_index[col].append((s, idx))

        return {"matching_unit_columns": list(common_cols), "cross_index": cross_index}

    # ------------------------------------------------------------------
    # Mutation — add / remove  (replaces mutate())
    # ------------------------------------------------------------------

    def add(
        self,
        target,
        expr_or_column,
        expression: str | None = None,
        inplace: bool = True,
    ) -> "Source":
        """Add a computed column to a sub-source.

        Signatures:
            s.add(s["fire"]["burn_rate"], "mean(fire[acres_burned]) * 2.5")
            s.add(("fire", "new_col"),    expr_string)
            s.add(("fire", "new_col"),    column_object)
        """
        from app.expressions.axis_expr import AxisExpr
        from app.mappings.column import Column
        from app.expressions.expr_parser import eval_expression

        target_source = self if inplace else self.clone()

        # Determine destination source + column name
        if isinstance(target, AxisExpr):
            dst_key = target._source_key
            dst_col = target._col_name
        elif isinstance(target, tuple):
            dst_key, dst_col = target
        elif isinstance(target, str):
            # "fire.new_col" or just "new_col" on first source
            if "." in target:
                dst_key, dst_col = target.split(".", 1)
            else:
                dst_key = next(iter(target_source.dataframes), None)
                dst_col = target
        else:
            raise TypeError(f"Unsupported target type {type(target)}")

        if dst_key not in target_source.dataframes:
            raise KeyError(f"Source '{dst_key}' not found")

        df = target_source.dataframes[dst_key]

        # Determine value to assign
        if isinstance(expr_or_column, Column):
            series = expr_or_column.data.reset_index(drop=True)
            if len(series) > len(df):
                series = series.iloc[: len(df)]
            series.index = df.index
            df[dst_col] = series
        elif isinstance(expr_or_column, str):
            result = eval_expression(expr_or_column, target_source, len(df))
            result.index = df.index
            df[dst_col] = result
        elif isinstance(expr_or_column, AxisExpr):
            series = expr_or_column.resolve()
            series.index = df.index[: len(series)]
            df[dst_col] = series

        return target_source

    def remove(self, target) -> "Source":
        """Remove a column, row range, or entire sub-source.

        Accepts:
            s["fire"]["col"]     AxisExpr  → remove the column
            ("fire", "col")      tuple     → remove column by name
            ("fire", "1..3")     tuple     → remove rows by DSL slice
            "fire"               str       → remove entire sub-source
        """
        from app.expressions.axis_expr import AxisExpr
        from app.indexing.index_parser import parse_row_index

        if isinstance(target, AxisExpr):
            src_key, col = target._source_key, target._col_name
            if src_key in self.dataframes and col in self.dataframes[src_key].columns:
                self.dataframes[src_key] = self.dataframes[src_key].drop(columns=[col])

        elif isinstance(target, tuple) and len(target) == 2:
            src_key, selector = target
            if src_key not in self.dataframes:
                return self
            df = self.dataframes[src_key]
            # Column removal
            if selector in df.columns:
                self.dataframes[src_key] = df.drop(columns=[selector])
            else:
                # Row range removal via DSL
                row_idx = parse_row_index(str(selector))
                if isinstance(row_idx, slice):
                    drop_positions = range(*row_idx.indices(len(df)))
                    self.dataframes[src_key] = df.drop(index=df.index[list(drop_positions)]).reset_index(drop=True)

        elif isinstance(target, str):
            self.dataframes.pop(target, None)
            self.source_definitions.pop(target, None)
            self.metadata.pop(target, None)

        return self

    def if_(self, condition) -> "ConditionalMutator":
        return ConditionalMutator(self, condition)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def log_regression(
        self,
        source_key: str,
        features: List[str],
        target: str,
    ) -> "RegressionResult":
        """Run logistic / linear regression and return a typed RegressionResult."""
        from app.analysis.results import RegressionResult

        if source_key not in self.dataframes:
            return RegressionResult(weights=[], bias=0.0, r2=0.0,
                                    feature_cols=features, target_col=target)

        df = self.dataframes[source_key].dropna(subset=features + [target])
        if df.empty:
            return RegressionResult(weights=[], bias=0.0, r2=0.0,
                                    feature_cols=features, target_col=target)
        try:
            from sklearn.linear_model import LinearRegression
            X = df[features]
            y = df[target]
            model = LinearRegression().fit(X, y)
            return RegressionResult(
                weights=list(model.coef_),
                bias=float(model.intercept_),
                r2=float(model.score(X, y)),
                feature_cols=features,
                target_col=target,
                points=df[features + [target]].copy(),
            )
        except ImportError:
            corrs = {col: float(df[col].corr(df[target])) for col in features}
            return RegressionResult(
                weights=list(corrs.values()),
                bias=0.0,
                r2=0.0,
                feature_cols=features,
                target_col=target,
            )

    def knn(
        self,
        source_key: str,
        features: List[str],
        target: str,
        n_neighbors: int = 3,
    ) -> "KNNResult":
        """Run KNN and return a typed KNNResult."""
        from app.analysis.results import KNNResult

        if source_key not in self.dataframes:
            return KNNResult(n_neighbors=n_neighbors, model_type="unknown",
                             feature_cols=features, target_col=target)

        df = self.dataframes[source_key].dropna(subset=features + [target])
        if df.empty:
            return KNNResult(n_neighbors=n_neighbors, model_type="unknown",
                             feature_cols=features, target_col=target)
        try:
            from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
            from sklearn.utils.multiclass import type_of_target
            X = df[features]
            y = df[target]
            y_type = type_of_target(y)
            if y_type == "continuous":
                model = KNeighborsRegressor(n_neighbors=n_neighbors).fit(X, y)
                model_type = "regressor"
                classes: list = []
            else:
                model = KNeighborsClassifier(n_neighbors=n_neighbors).fit(X, y)
                model_type = "classifier"
                classes = list(model.classes_)
            return KNNResult(
                n_neighbors=n_neighbors,
                model_type=model_type,
                feature_cols=features,
                target_col=target,
                points=df[features + [target]].copy(),
                classes=classes,
            )
        except ImportError:
            return KNNResult(n_neighbors=n_neighbors, model_type="fallback",
                             feature_cols=features, target_col=target)

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def bar(self, x_expr: "AxisExpr", y_expr: "AxisExpr") -> "Chart":
        from app.visualizations.chart import Chart
        return Chart("bar", x_expr, y_expr)

    def scatter(self, x_expr: "AxisExpr", y_expr: "AxisExpr") -> "Chart":
        from app.visualizations.chart import Chart
        return Chart("scatter", x_expr, y_expr)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _empty_clone(self) -> "Source":
        new_s = Source()
        new_s.key = f"{self.key}_sub"
        new_s.source_definitions = dict(self.source_definitions)
        new_s.metadata = dict(self.metadata)
        new_s.mappings = dict(self.mappings)
        new_s._named_roles = {k: dict(v) for k, v in self._named_roles.items()}
        new_s._registered_maps = dict(self._registered_maps)
        return new_s

    def __repr__(self) -> str:
        sources = list(self.dataframes.keys())
        return f"Source(key={self.key!r}, sub_sources={sources})"


# ---------------------------------------------------------------------------
# ConditionalMutator
# ---------------------------------------------------------------------------

class ConditionalMutator:
    """Returned by Source.if_() — chains .add() and .remove() with a condition."""

    def __init__(self, source: Source, condition):
        self.source = source
        self.condition = condition

    def add(self, target, expr_or_column, inplace: bool = True) -> Source:
        # Wrap expression so it only writes rows that satisfy condition
        from app.expressions.axis_expr import AxisExpr
        from app.expressions.expr_parser import eval_expression

        dst_key = (
            target._source_key if isinstance(target, AxisExpr)
            else target[0] if isinstance(target, tuple)
            else next(iter(self.source.dataframes), None)
        )
        dst_col = (
            target._col_name if isinstance(target, AxisExpr)
            else target[1] if isinstance(target, tuple)
            else str(target)
        )

        if dst_key not in self.source.dataframes:
            return self.source

        df = self.source.dataframes[dst_key]

        # Build mask from condition
        try:
            if isinstance(self.condition, AxisExpr):
                mask = self.condition.resolve().values[:len(df)]
            else:
                mask = df.eval(str(self.condition))
        except Exception:
            mask = [True] * len(df)

        # Evaluate expression
        if isinstance(expr_or_column, str):
            result = eval_expression(expr_or_column, self.source, len(df))
        elif isinstance(expr_or_column, AxisExpr):
            result = expr_or_column.resolve()
        else:
            import pandas as _pd
            result = _pd.Series([expr_or_column] * len(df))

        result.index = df.index

        if dst_col not in df.columns:
            df[dst_col] = None
        df.loc[mask, dst_col] = result[mask]

        return self.source

    # Keep backward-compat .mutate() pointing at .add()
    def mutate(self, operation, inplace: bool = True, **kwargs) -> Source:
        kwargs["_condition"] = self.condition
        return self.source.add(
            (kwargs.get("source_key", next(iter(self.source.dataframes))),
             kwargs.get("output_col", "__out__")),
            kwargs.get("expression", "0"),
            inplace=inplace,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def source(key_or_def: str | SourceDefinition) -> Source:
    """Convenience factory — `from app.workflow import source`."""
    return Source(key_or_def)
