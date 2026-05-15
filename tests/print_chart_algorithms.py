"""
Printable direct-backend exercise for every supported chart and analysis path.

Run from repo root:
    python tests/print_chart_algorithms.py

This is intentionally not a pytest file. It prints rows, chart outputs, and
analysis results so you can inspect the behavior directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.workflow import analysis_tools, bind_sources, charts, source


def write_demo_sources(base: Path) -> tuple[Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    a_path = base / "chart_source_a.csv"
    b_path = base / "chart_source_b.csv"

    a_path.write_text(
        "year,county,state,latitude,longitude,metric_name,metric_value,category,heat_x,heat_y,heat_z,source,target,value\n"
        "2019,Lane,OR,44.05,-123.08,fire,10,A,1,1,10,ignition,response,10\n"
        "2020,Lane,OR,44.10,-123.04,fire,20,A,1,2,20,response,recovery,7\n"
        "2021,Multnomah,OR,45.51,-122.68,fire,35,B,2,1,35,ignition,recovery,4\n"
        "2022,Jackson,OR,42.33,-122.87,other,15,B,2,2,15,recovery,mitigation,5\n",
        encoding="utf-8",
    )
    b_path.write_text(
        "year,county,state,latitude,longitude,metric_name,metric_value,category,heat_x,heat_y,heat_z,source,target,value\n"
        "2019,Lane,OR,44.06,-123.09,fire,12,A,1,1,12,ignition,response,8\n"
        "2020,Deschutes,OR,44.06,-121.31,fire,25,C,1,2,25,response,mitigation,6\n"
        "2021,Multnomah,OR,45.52,-122.67,fire,30,B,2,1,30,ignition,recovery,9\n"
        "2022,Jackson,OR,42.34,-122.88,other,18,B,2,2,18,recovery,mitigation,3\n",
        encoding="utf-8",
    )
    return a_path, b_path


def main() -> None:
    artifact_dir = Path("artifacts/print_chart_algorithms")
    a_path, b_path = write_demo_sources(artifact_dir)

    columns = ["year", "county", "state", "latitude", "longitude", "metric_name", "metric_value", "category", "heat_x", "heat_y", "heat_z", "source", "target", "value"]
    a = source("print_a", str(a_path), column_hints=columns)
    b = source("print_b", str(b_path), column_hints=columns)
    combined = bind_sources(a, b)
    combined.year_range(2019, 2022, source_keys=["print_a", "print_b"])

    rows_a = combined.fetch(source_keys=["print_a"], limit=100, print_rows=True)
    rows_b = combined.fetch(source_keys=["print_b"], limit=100, print_rows=True)
    all_rows = rows_a + rows_b
    rows_by_source = {"print_a": rows_a, "print_b": rows_b}

    print("\nROW COUNTS")
    print({"print_a": len(rows_a), "print_b": len(rows_b), "combined": len(all_rows)})

    chart = charts()
    chart.scatter(a, "year", "metric_value", name="scatter_metric_by_year")
    chart.bar(a, "metric_value", "county", name="bar_county_metric")
    chart.metric(
        combined,
        "metric_two_sources",
        [
            {"source_key": "print_a", "x": "year", "y": "metric_value", "label": "A"},
            {"source_key": "print_b", "x": "year", "y": "metric_value", "label": "B"},
        ],
    )
    chart.overlay(combined, "overlay_year_metric", [("print_a", ("year", "metric_value")), ("print_b", ("year", "metric_value"))])
    chart.sankey(combined, "sankey_flow")
    chart.heatmap(a, "heatmap_metric", "heat_x", "heat_y", "heat_z")
    chart.correlation_matrix(combined, "correlation_matrix", variables=["year", "metric_value", "heat_z"])
    chart.cross_pair(
        combined,
        "cross_pair_sources",
        ("print_a", "year", "metric_value"),
        ("print_b", "year", "metric_value"),
    )
    chart.foreach_expand(a, "year", "heat_z", "metric_value", "heat_z", name_prefix="foreach_pairs", kinds=("scatter", "bar"))

    outputs = chart.render_python(rows_by_source, artifact_dir / "charts")
    print("\nCHART DEFINITIONS")
    for definition in chart.definitions:
        print({k: definition[k] for k in definition.keys() if k in {"type", "name", "name_prefix"}})

    print("\nPLOT OUTPUTS")
    for output in outputs:
        print(output)

    tools = analysis_tools()
    combined.average_step("metric_value", group_by="county")
    combined.distribution_step("metric_value", bins=4)
    combined.probability_step("metric_name", "fire")
    combined.bayes_step("metric_name", "fire", "county", "Lane")
    combined.region_distance_step()
    combined.intersection_step(radius_km=12)
    combined.regression_step("year", "metric_value")

    print("\nANALYSIS STEP RESULTS")
    for result in combined.run_analysis_steps(all_rows, tools=tools):
        print(result)

    print("\nDIRECT ANALYSIS TOOLS")
    print("correlation", tools.correlation(all_rows, variables=["year", "metric_value", "heat_z"]))
    print("regression", tools.regression(all_rows, x="year", y="metric_value"))
    print("county_compare", tools.county_compare(all_rows))
    print("available_backends", tools.available_backends())


if __name__ == "__main__":
    main()
