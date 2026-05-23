import shutil
import sys
import tempfile
from pathlib import Path

import pytest


API_ROOT = Path(__file__).resolve().parent.parent
TEST_TMP_ROOT = API_ROOT / "tests" / ".tmp"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture
def tmp_path():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="pytest-", dir=TEST_TMP_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
