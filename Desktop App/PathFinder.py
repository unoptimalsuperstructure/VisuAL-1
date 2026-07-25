import sys
from pathlib import Path

def resource_path(relative_path: str) -> Path:
    base = Path(__file__).resolve().parent
    return base / relative_path