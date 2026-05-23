import gc
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest


API_ROOT = Path(__file__).resolve().parent.parent
TEST_TMP_ROOT = API_ROOT / "tests" / ".tmp"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture
def repo_tmp_path():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="pytest-", dir=TEST_TMP_ROOT))
    yield path
    gc.collect()
    for _ in range(20):
        try:
            shutil.rmtree(path)
            break
        except PermissionError:
            time.sleep(0.1)
    else:
        shutil.rmtree(path)
