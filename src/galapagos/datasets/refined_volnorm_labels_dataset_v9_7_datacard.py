from __future__ import annotations

from typing import Any

from galapagos.datasets.refined_volnorm_labels_dataset_v9_7 import build_markdown_v9_7


def build_refined_volnorm_labels_dataset_datacard_v9_7(report: dict[str, Any]) -> str:
    return build_markdown_v9_7(report)
