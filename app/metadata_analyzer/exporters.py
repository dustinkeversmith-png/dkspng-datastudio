import csv
from typing import List, Dict, Any
from app.metadata_analyzer.schemas import DatasetProfile

def export_to_json(profile: DatasetProfile, filepath: str) -> None:
    profile.export_to_json(filepath)

def export_to_csv(profile: DatasetProfile, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Column Name", "Inferred Type", "Unit/Tag", "Null Count", "Unique Values", "Human Description"])
        for col in profile.columns:
            writer.writerow([
                col.name,
                col.inferred_type,
                col.inferred_unit_tag or "",
                col.null_count,
                col.unique_values,
                col.human_description or ""
            ])

def export_to_markdown(profile: DatasetProfile, patch_data: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Data Identity Card: {profile.source_key}\n\n")
        f.write("## Source Lineage\n")
        f.write(f"- **URL**: {profile.source_url}\n")
        f.write(f"- **Fetched At**: {profile.fetch_timestamp}\n")
        f.write(f"- **Patch Row Count**: {profile.row_count}\n\n")
        
        f.write("## Column Index\n")
        f.write("| Column Name | Inferred Type | Unit/Tag | Nulls | Unique | Description |\n")
        f.write("|-------------|---------------|----------|-------|--------|-------------|\n")
        for col in profile.columns:
            unit = col.inferred_unit_tag or "-"
            desc = col.human_description or "-"
            f.write(f"| {col.name} | {col.inferred_type} | {unit} | {col.null_count} | {col.unique_values} | {desc} |\n")
        
        f.write("\n## Data Sample (Top 5 Rows)\n")
        sample = patch_data[:5]
        if sample:
            headers = list(sample[0].keys())
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---" for _ in headers]) + "|\n")
            for row in sample:
                vals = [str(row.get(h, "")).replace('\n', ' ') for h in headers]
                f.write("| " + " | ".join(vals) + " |\n")
