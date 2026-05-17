from __future__ import annotations

from pathlib import Path

from galapagos.research.causal_feature_readiness.seed_reader import SeedReadinessReader


class FeaturePreviewSeedReader(SeedReadinessReader):
    def assert_healthy(self) -> dict[str, object]:
        audit = self.audit()
        if (
            audit["missing_seed_files_count"] != 0
            or audit["unexpected_seed_files_count"] != 0
            or audit["seed_json_valid"] is not True
            or audit["seed_checksums_verified"] is not True
        ):
            raise ValueError(f"Seed is not healthy for feature preview: {audit}")
        return audit


def seed_reader(root: Path) -> FeaturePreviewSeedReader:
    return FeaturePreviewSeedReader(root)
