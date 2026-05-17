import json
import os

class MicrostructureReportWriter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def write_report(self, name: str, data: dict):
        json_path = os.path.join(self.output_dir, f"{name}.json")
        md_path = os.path.join(self.output_dir, f"{name}.md")
        
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        with open(md_path, 'w') as f:
            f.write(f"# {name.replace('_', ' ').title()}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
