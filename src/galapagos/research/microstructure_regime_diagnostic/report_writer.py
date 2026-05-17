"""Write diagnostic reports for V1.49."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def write_json_report(data: dict[str, Any], path: str | Path) -> None:
    """Write diagnostic data to JSON."""
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

def write_markdown_report(data: dict[str, Any], path: str | Path, title: str) -> None:
    """Write diagnostic summary to Markdown."""
    lines = [f"# {title}", ""]
    
    if "status" in data:
        lines.append(f"- Status: {data['status']}")
        
    if "regime_stats" in data:
        lines.append("## Regime Statistics")
        stats = data["regime_stats"]
        for r, count in stats.get("regime_counts", {}).items():
            pct = stats.get("regime_percentages", {}).get(r, 0)
            lines.append(f"- **{r}**: {count} rows ({pct:.2f}%)")
            
    if "failure_2026_analysis" in data:
        lines.append("## 2026 Failure Analysis")
        fail = data["failure_2026_analysis"]
        lines.append(f"- Explaining regimes: {fail.get('explaining_regimes', [])}")
        
    Path(path).write_text("\n".join(lines), encoding="utf-8")
