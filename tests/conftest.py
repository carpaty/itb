"""Shared test setup: example configs and an in-memory state cache."""

import shutil
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"

for _target in (SRC / "menu.yaml", SRC / "calls" / "button_func.py"):
    if not _target.exists():
        shutil.copy(f"{_target}.example", _target)


class FakeCache:
    """In-memory replacement for db.Cache."""

    def __init__(self):
        self.data = {}

    def qselect(self, name):
        """Return a stored value."""
        return self.data.get(name)

    def qinsert(self, name, val):
        """Store a value."""
        self.data[name] = dict(val)

    def qdelete(self, name):
        """Remove a value."""
        self.data.pop(name, None)


@pytest.fixture
def cache(monkeypatch):
    """Replace the Datastore backed state cache with an in-memory one."""
    import utils  # pylint: disable=import-outside-toplevel
    fake = FakeCache()
    monkeypatch.setattr(utils, "cache", fake)
    return fake
