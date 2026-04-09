from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gui.app import run

if __name__ == "__main__":
    run()
