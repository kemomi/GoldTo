import os
import sys
import uuid
from pathlib import Path

import pytest


API_ROOT = Path(__file__).resolve().parent.parent
TEST_TMP_ROOT = API_ROOT / "tests" / ".tmp"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def isolated_demo_database(request: pytest.FixtureRequest):
    test_name = request.node.name.replace(os.sep, "-").replace(":", "-")
    database_path = TEST_TMP_ROOT / f"{test_name}-{uuid.uuid4().hex}.sqlite"
    os.environ["APP_DATABASE_PATH"] = str(database_path)
    yield


@pytest.fixture
def repo_tmp_path():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    yield TEST_TMP_ROOT
