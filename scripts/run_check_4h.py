from __future__ import annotations

import sys

from scripts.run_cycle import main

if __name__ == "__main__":
    if "--profile" not in sys.argv:
        sys.argv.extend(["--profile", "4h"])
    main()

