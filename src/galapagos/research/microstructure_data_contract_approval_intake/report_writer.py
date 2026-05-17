import json
from pathlib import Path
from typing import Any, Dict


class ReportWriter:
    """Écrit des rapports JSON+MD dans un répertoire cible.

    Le répertoire est passé à la construction – pour V1.81.7 c'est
    ``reports/research/``, pour V1.81.6 c'était ``reports/``.
    """

    def __init__(self, version: str, output_dir: str = "reports"):
        self.v_disp = version
        self.output_dir = Path(output_dir)
        self.version_suffix = version.replace(".", "_").lower()
        if not self.version_suffix.startswith("v"):
            self.version_suffix = "v" + self.version_suffix
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, data: Dict[str, Any]) -> Path:
        """Écrit un fichier JSON. Retourne le chemin écrit."""
        full_name = name  # Le nom doit déjà contenir le suffixe de version
        json_p = self.output_dir / f"{full_name}.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(json_p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return json_p

    def write_md(self, name: str, content: str) -> Path:
        """Écrit un fichier Markdown. Retourne le chemin écrit."""
        md_p = self.output_dir / f"{name}.md"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(md_p, "w", encoding="utf-8") as f:
            f.write(content)
        return md_p

    def write_report(self, name: str, data: Dict[str, Any]) -> None:
        """Rétrocompatibilité : écrit JSON + MD généré automatiquement."""
        self.write_json(name, data)
        md_content = (
            f"# {name.replace('_', ' ').title()}\n\n"
            f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n"
        )
        self.write_md(name, md_content)
