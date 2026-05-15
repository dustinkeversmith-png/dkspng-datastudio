"""
Processing pipeline for visualization-session rows (dict records).

Steps are applied in order. Rows are expected to carry ``session_dataset_id``
when multiple bindings exist so per-dataset operations can target one stream.

Rows from merged session queries should include ``session_source_key`` so
``reference_scope`` can narrow transforms without guessing dataset ids.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, TypeAdapter


class ExcludeColumnsStep(BaseModel):
    type: Literal["exclude_columns"] = "exclude_columns"
    columns: list[str]
    dataset_id: str | None = None


class IncludeColumnsStep(BaseModel):
    type: Literal["include_columns"] = "include_columns"
    columns: list[str]
    dataset_id: str | None = None


class RenameColumnsStep(BaseModel):
    type: Literal["rename_columns"] = "rename_columns"
    mapping: dict[str, str]
    dataset_id: str | None = None


class JoinStep(BaseModel):
    type: Literal["join"] = "join"
    left_dataset_id: str
    right_dataset_id: str
    on: list[str]
    how: Literal["inner", "left", "outer"] = "inner"
    suffixes: tuple[str, str] = ("_left", "_right")


class ReferenceScopeStep(BaseModel):
    """Narrow subsequent transforms to rows whose ``session_source_key`` is listed."""

    type: Literal["reference_scope"] = "reference_scope"
    source_keys: list[str]
    mode: Literal["union", "replace"] = "union"


class ExcludeRowsStep(BaseModel):
    """Drop rows by 0-based indices into the **current** row list (after prior steps)."""

    type: Literal["exclude_rows"] = "exclude_rows"
    indices: list[int]
    dataset_id: str | None = None


class StackColumnsStep(BaseModel):
    """Wide → long: melt ``measure_vars`` into ``variable`` / ``value`` pairs."""

    type: Literal["stack_columns"] = "stack_columns"
    id_vars: list[str]
    measure_vars: list[str]
    var_name: str = "variable"
    value_name: str = "value"
    dataset_id: str | None = None


PipelineStepType = (
    ExcludeColumnsStep
    | IncludeColumnsStep
    | RenameColumnsStep
    | JoinStep
    | ReferenceScopeStep
    | ExcludeRowsStep
    | StackColumnsStep
)

_pipeline_adapter = TypeAdapter(PipelineStepType)


def validate_pipeline_steps(steps: list[dict]) -> None:
    for raw in steps:
        _pipeline_adapter.validate_python(raw)


def _pick_columns(row: dict, keep: set[str]) -> dict:
    return {k: v for k, v in row.items() if k in keep}


def _row_in_scope(row: dict, active: set[str] | None) -> bool:
    if active is None:
        return True
    sk = row.get("session_source_key")
    if sk is None:
        return True
    return sk in active


def _partition_scope(rows: list[dict], active: set[str] | None) -> tuple[list[dict], list[dict]]:
    if active is None:
        return rows, []
    in_scope: list[dict] = []
    out_scope: list[dict] = []
    for row in rows:
        if _row_in_scope(row, active):
            in_scope.append(row)
        else:
            out_scope.append(row)
    return in_scope, out_scope


def _merge_partitioned(out_scope: list[dict], transformed: list[dict]) -> list[dict]:
    # Transformed (in-scope) rows first so previews read naturally after a reference_scope.
    return transformed + out_scope


def _apply_exclude(rows: list[dict], columns: set[str], dataset_id: str | None) -> list[dict]:
    out = []
    for row in rows:
        if dataset_id is not None and row.get("session_dataset_id") != dataset_id:
            out.append(row)
            continue
        out.append({k: v for k, v in row.items() if k not in columns})
    return out


def _apply_include(rows: list[dict], columns: set[str], dataset_id: str | None) -> list[dict]:
    meta = {"session_dataset_id", "session_source_key", "source_key", "id"}
    keep = columns | meta
    out = []
    for row in rows:
        if dataset_id is not None and row.get("session_dataset_id") != dataset_id:
            out.append(row)
            continue
        out.append(_pick_columns(row, keep))
    return out


def _apply_rename(rows: list[dict], mapping: dict[str, str], dataset_id: str | None) -> list[dict]:
    out = []
    for row in rows:
        if dataset_id is not None and row.get("session_dataset_id") != dataset_id:
            out.append(row)
            continue
        new_row = {}
        for k, v in row.items():
            new_row[mapping.get(k, k)] = v
        out.append(new_row)
    return out


def _apply_exclude_rows(rows: list[dict], drop: set[int], dataset_id: str | None) -> list[dict]:
    out: list[dict] = []
    if dataset_id is None:
        for i, row in enumerate(rows):
            if i in drop:
                continue
            out.append(row)
        return out

    # Per-dataset row numbering: indices refer to rows belonging to dataset_id only.
    idx = 0
    for row in rows:
        if row.get("session_dataset_id") != dataset_id:
            out.append(row)
            continue
        if idx in drop:
            idx += 1
            continue
        out.append(row)
        idx += 1
    return out


def _apply_stack(
    rows: list[dict],
    id_vars: list[str],
    measure_vars: list[str],
    var_name: str,
    value_name: str,
    dataset_id: str | None,
) -> list[dict]:
    id_set = set(id_vars)
    out: list[dict] = []
    for row in rows:
        if dataset_id is not None and row.get("session_dataset_id") != dataset_id:
            out.append(dict(row))
            continue
        base = {k: v for k, v in row.items() if k not in measure_vars and k in id_set}
        for m in measure_vars:
            if m not in row:
                continue
            r = dict(base)
            r[var_name] = m
            r[value_name] = row.get(m)
            for k, v in row.items():
                if k in id_set or k in measure_vars:
                    continue
                if k not in r:
                    r[k] = v
            out.append(r)
    return out


def _split_by_dataset(rows: list[dict], dataset_id: str) -> list[dict]:
    return [r for r in rows if r.get("session_dataset_id") == dataset_id]


def _join_rows(
    left: list[dict],
    right: list[dict],
    on: list[str],
    how: Literal["inner", "left", "outer"],
    suffixes: tuple[str, str],
) -> list[dict]:
    if not on:
        return []

    def key(row: dict) -> tuple:
        return tuple(row.get(c) for c in on)

    right_buckets: dict[tuple, list[dict]] = {}
    for r in right:
        right_buckets.setdefault(key(r), []).append(r)

    result: list[dict] = []

    for lrow in left:
        k = key(lrow)
        matches = right_buckets.get(k, [])
        if not matches:
            if how in ("left", "outer"):
                merged = {**lrow}
                for rk in right[0].keys() if right else []:
                    if rk not in merged and rk not in on:
                        merged[f"{rk}{suffixes[1]}"] = None
                result.append(merged)
            continue
        for rrow in matches:
            merged = {**lrow}
            for rk, rv in rrow.items():
                if rk in on:
                    continue
                target = rk if rk not in merged else f"{rk}{suffixes[1]}"
                merged[target] = rv
            if "session_source_key" not in merged and rrow.get("session_source_key"):
                merged["session_source_key"] = rrow.get("session_source_key")
            result.append(merged)

    if how == "outer":
        for rrow in right:
            k = key(rrow)
            if not any(key(lr) == k for lr in left):
                merged = {**rrow}
                for lk in left[0].keys() if left else []:
                    if lk not in merged and lk not in on:
                        merged[f"{lk}{suffixes[0]}"] = None
                result.append(merged)

    return result


def _apply_join_step(rows: list[dict], step: JoinStep) -> list[dict]:
    left = _split_by_dataset(rows, step.left_dataset_id)
    right = _split_by_dataset(rows, step.right_dataset_id)
    joined = _join_rows(left, right, step.on, step.how, step.suffixes)
    rest = [
        r
        for r in rows
        if r.get("session_dataset_id")
        not in (step.left_dataset_id, step.right_dataset_id)
    ]
    return rest + joined


def apply_pipeline(rows: list[dict], steps: list) -> list[dict]:
    """Apply manipulation steps. ``steps`` are Pydantic pipeline models or dicts."""
    current = [dict(r) for r in rows]
    active: set[str] | None = None

    for raw in steps:
        if isinstance(raw, dict):
            step = _pipeline_adapter.validate_python(raw)
        else:
            step = raw

        if isinstance(step, ReferenceScopeStep):
            keys = [k for k in step.source_keys if k]
            if step.mode == "replace":
                active = set(keys)
            else:
                active = (active or set()) | set(keys)
            continue

        def apply_transform(target: list[dict]) -> list[dict]:
            if isinstance(step, ExcludeColumnsStep):
                return _apply_exclude(target, set(step.columns), step.dataset_id)
            if isinstance(step, IncludeColumnsStep):
                return _apply_include(target, set(step.columns), step.dataset_id)
            if isinstance(step, RenameColumnsStep):
                return _apply_rename(target, step.mapping, step.dataset_id)
            if isinstance(step, JoinStep):
                return _apply_join_step(target, step)
            if isinstance(step, ExcludeRowsStep):
                return _apply_exclude_rows(target, set(step.indices), step.dataset_id)
            if isinstance(step, StackColumnsStep):
                return _apply_stack(
                    target,
                    step.id_vars,
                    step.measure_vars,
                    step.var_name,
                    step.value_name,
                    step.dataset_id,
                )
            raise TypeError(f"Unsupported step: {type(step)}")

        in_scope, out_scope = _partition_scope(current, active)
        transformed = apply_transform(in_scope)
        current = _merge_partitioned(out_scope, transformed)

    return current
