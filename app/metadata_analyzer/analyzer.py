import re
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.metadata_analyzer.schemas import ColumnProfile, DatasetProfile

class MetadataAnalyzer:
    def __init__(self, source_key: str, source_url: str, context_map_path: str = "app/metadata_analyzer/context_map.json"):
        self.source_key = source_key
        self.source_url = source_url
        self.context_map = {}
        
        if os.path.exists(context_map_path):
            try:
                with open(context_map_path, "r", encoding="utf-8") as f:
                    self.context_map = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load context map from {context_map_path}. {e}")

    def generate_profile(self, patch_data: List[Dict[str, Any]], human_overrides: Optional[Dict[str, str]] = None) -> DatasetProfile:
        human_overrides = human_overrides or {}
        
        if not patch_data:
            return DatasetProfile(
                source_key=self.source_key,
                source_url=self.source_url,
                fetch_timestamp=datetime.utcnow().isoformat(),
                row_count=0,
                columns=[]
            )

        total_rows = len(patch_data)
        columns = list(patch_data[0].keys())
        column_profiles = []

        for col in columns:
            # Gather stats
            values = [row.get(col) for row in patch_data]
            null_count = sum(1 for v in values if v is None or v == "")
            non_null_values = [v for v in values if v is not None and v != ""]
            unique_values = len(set(non_null_values))

            # Heuristic Inference
            inferred_type = "string"
            inferred_unit_tag = None

            # Geo-Coordinates
            if re.search(r'(lat|lon|y_coord|x_coord)', col, re.IGNORECASE):
                try:
                    num_vals = [float(v) for v in non_null_values if str(v).replace('.', '', 1).replace('-', '', 1).isdigit()]
                    if num_vals and all(-180 <= v <= 180 for v in num_vals):
                        inferred_unit_tag = "decimal_degrees"
                        inferred_type = "float"
                except:
                    pass

            # Financials
            elif re.search(r'(cost|earnings|suppression_cost)', col, re.IGNORECASE) or any(isinstance(v, str) and str(v).startswith('$') for v in non_null_values):
                inferred_unit_tag = "USD"
                inferred_type = "currency"

            # Dates and Temporal
            elif re.search(r'(^|_)(year|month|day|date|time|date_range)($|_)', col, re.IGNORECASE):
                inferred_unit_tag = "temporal"
                inferred_type = "datetime"

            # Dimensions and Measurements
            elif re.search(r'(length|width|depth|height|slope|area|volume|radius)', col, re.IGNORECASE) or re.search(r'_(ft|m|in|cm|km|mi|ft2|ft3|m2|m3)$', col, re.IGNORECASE):
                suffix_match = re.search(r'_(ft|m|in|cm|km|mi|ft2|ft3|m2|m3)$', col, re.IGNORECASE)
                dim_match = re.search(r'(length|width|depth|height|slope|area|volume|radius)', col, re.IGNORECASE)
                inferred_unit_tag = suffix_match.group(1).lower() if suffix_match else (dim_match.group(1).lower() if dim_match else "measurement")
                inferred_type = "numeric"

            # Identifiers
            elif re.search(r'(^|_)(id|uuid|irwin|fod_id|fid)($|_)', col, re.IGNORECASE):
                inferred_unit_tag = "unique_identifier"
                inferred_type = "string"

            # Categorical
            elif total_rows > 0 and (unique_values / total_rows < 0.1) and unique_values < 50:
                inferred_unit_tag = "label_lookup"
                inferred_type = "categorical"

            # Fallback simple type inference
            if inferred_type == "string" and non_null_values:
                # check if mostly numeric
                num_count = sum(1 for v in non_null_values if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).replace('-', '', 1).isdigit()))
                if num_count == len(non_null_values):
                    inferred_type = "numeric"

            # Human Description
            human_desc = human_overrides.get(col) or self.context_map.get(col)

            column_profiles.append(ColumnProfile(
                name=col,
                inferred_type=inferred_type,
                inferred_unit_tag=inferred_unit_tag,
                null_count=null_count,
                unique_values=unique_values,
                human_description=human_desc
            ))

        return DatasetProfile(
            source_key=self.source_key,
            source_url=self.source_url,
            fetch_timestamp=datetime.utcnow().isoformat(),
            row_count=total_rows,
            columns=column_profiles
        )
