from pathlib import Path
import sys


API_ROOT = Path(__file__).resolve().parent.parent

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
