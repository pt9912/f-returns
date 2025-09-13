import os
import pathlib
import sys

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
