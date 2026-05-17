import json
from pathlib import Path

def load_source_artifacts(summary_path, eval_path, temp_path, proxy_path):
    artifacts = {}
    paths = {
        "summary": summary_path,
        "evaluation": eval_path,
        "temporal": temp_path,
        "proxy": proxy_path
    }
    
    for key, path in paths.items():
        p = Path(path)
        if p.exists():
            with open(p) as f:
                artifacts[key] = json.load(f)
        else:
            artifacts[key] = None
            
    return artifacts

def load_mismatch_artifacts(mismatch_path):
    p = Path(mismatch_path)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None
