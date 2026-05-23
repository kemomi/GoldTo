import gc
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

import pytest


API_ROOT = Path(__file__).resolve().parent.parent
TEST_TMP_ROOT = API_ROOT / "tests" / ".tmp"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def isolated_demo_database(test_tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_DATABASE_PATH", str(test_tmp_path / "demo.sqlite"))
    yield


@pytest.fixture
def test_tmp_path(request: pytest.FixtureRequest):
    test_name = request.node.name.replace(os.sep, "-").replace(":", "-")
    path = TEST_TMP_ROOT / f"{test_name}-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    yield path
    gc.collect()
    for _ in range(40):
        try:
            shutil.rmtree(path)
            break
        except FileNotFoundError:
            break
        except PermissionError:
            time.sleep(0.05)
    else:
        shutil.rmtree(path)


@pytest.fixture
def repo_tmp_path(test_tmp_path: Path):
    yield test_tmp_path
