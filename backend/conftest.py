"""Pytest configuration for the Recall backend.

Uses an isolated, per-session SQLite file via the RECALL_DB_PATH env var so
tests never touch the developer's real data. Each test starts from a fresh DB.
"""
import os
import tempfile

os.environ["RECALL_DB_PATH"] = tempfile.mktemp(suffix=".db")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    path = os.environ["RECALL_DB_PATH"]
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
    yield
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
