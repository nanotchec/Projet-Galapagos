import os
from pathlib import Path

class SafetyGuard:
    """Garde-fou strict pour empêcher toute écriture réelle lors du dry-run."""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = data_root

    def verify_no_write(self, initial_files: set) -> dict:
        """Vérifie qu'aucun fichier n'a été ajouté dans data/."""
        current_files = self.get_data_files()
        new_files = current_files - initial_files
        
        return {
            "data_directory_write_attempted": len(new_files) > 0,
            "new_data_files": list(new_files),
            "no_data_directory_writes": len(new_files) == 0
        }

    def get_data_files(self) -> set:
        data_path = Path(self.data_root)
        if not data_path.exists():
            return set()
        return {str(p.relative_to(data_path)) for p in data_path.rglob("*") if p.is_file()}
