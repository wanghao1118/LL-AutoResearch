"""Support both python3 -m auto_design and an absolute script path."""

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_design.cli import main

if __name__ == "__main__":
    main()
