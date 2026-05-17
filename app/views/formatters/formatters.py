import json
import csv
import io
from typing import Any
from app.views.base_formatter import BaseFormatter
from app.core.result import ComponentResult

class JSONFormatter(BaseFormatter):
    def format(self, result: ComponentResult) -> str:
        return json.dumps(result.data, indent=2)

class CSVFormatter(BaseFormatter):
    def format(self, result: ComponentResult) -> str:
        if result.data.get("type") != "table":
            raise ValueError("CSVFormatter can only format 'table' view structures.")
            
        headers = result.data.get("headers", [])
        rows = result.data.get("rows", [])
        
        output = io.StringIO()
        if not headers and rows:
            headers = list(rows[0].keys())
            
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Ensure rows only contain header keys, or write dict safely
        for row in rows:
            safe_row = {k: row.get(k) for k in headers}
            writer.writerow(safe_row)
            
        return output.getvalue()

class HTMLFormatter(BaseFormatter):
    def format(self, result: ComponentResult) -> str:
        data = result.data
        v_type = data.get("type")
        
        if v_type == "table":
            return self._format_table(data)
        elif v_type == "summary":
            return self._format_summary(data)
        elif v_type == "cards":
            return self._format_cards(data)
        else:
            return f"<div>Unsupported view type: {v_type}</div>"

    def _format_table(self, data: dict) -> str:
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        
        html = "<table>\n  <thead>\n    <tr>\n"
        for h in headers:
            html += f"      <th>{h}</th>\n"
        html += "    </tr>\n  </thead>\n  <tbody>\n"
        
        for row in rows:
            html += "    <tr>\n"
            for h in headers:
                html += f"      <td>{row.get(h, '')}</td>\n"
            html += "    </tr>\n"
            
        html += "  </tbody>\n</table>"
        return html

    def _format_summary(self, data: dict) -> str:
        html = f"<div>\n  <h3>Summary</h3>\n  <p>Total Records: {data.get('total_records')}</p>\n"
        html += "  <ul>\n"
        for col, stats in data.get("numeric_summaries", {}).items():
            html += f"    <li><strong>{col}</strong>: Mean={stats.get('mean'):.2f}, Min={stats.get('min')}, Max={stats.get('max')}</li>\n"
        html += "  </ul>\n</div>"
        return html

    def _format_cards(self, data: dict) -> str:
        cards = data.get("cards", [])
        html = "<div class='card-container'>\n"
        for card in cards:
            html += "  <div class='card'>\n"
            html += f"    <h4>{card.get('title')}</h4>\n"
            html += f"    <p>{card.get('description')}</p>\n"
            html += "  </div>\n"
        html += "</div>"
        return html
