"""Report writer for V1.45."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def write_research_report(
    name: str,
    payload: dict[str, Any],
    title: str,
    lines: list[str],
    output_dir: str = "reports/research"
) -> None:
    """Write both JSON and Markdown versions of a research report."""
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 1. JSON
    json_path = out_path / f"{name}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # 2. Markdown
    md_path = out_path / f"{name}.md"
    md_content = [f"# {title}\n"]
    md_content.extend([f"- {line}" for line in lines])
    md_content.append("\n## Data Preview\n")
    md_content.append("```json")
    md_content.append(json.dumps(payload, indent=2, ensure_ascii=False))
    md_content.append("```")
    
    md_path.write_text("\n".join(md_content), encoding="utf-8")

def generate_v1_45_summary_md(payload: dict[str, Any]) -> str:
    """Generate the main summary markdown for V1.45 research."""
    
    content = [
        f"# Feature Ablation & Causal Importance Research {payload['version']}",
        f"\n**Verdict Final** : `{payload['final_verdict']}`",
        f"\n**Prochaine Étape Recommandée** : {payload['recommended_next_step']}",
        f"\n- Evidence Classification : {payload['evidence_classification']}",
        f"- Improves over V1.44.4 : {payload['improves_over_v1_44_4']}",
        f"- Best Family : {payload['best_family_observed']}",
        f"- Worst Family : {payload['worst_family_observed']}",
        "\n## Safety Flags",
        f"- No Strategy Validated : {payload['no_strategy_validated']}",
        f"- No Real Trading : {payload['no_real_trading']}",
        f"- No Paper Live : {payload['no_paper_live']}",
        f"- No Preregistration : {payload['no_preregistration_yet']}",
    ]
    
    return "\n".join(content)
