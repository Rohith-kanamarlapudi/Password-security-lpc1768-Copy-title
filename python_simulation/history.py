"""Authentication history: a simple in-memory log for the current session.

The digits a user types are never stored here - only what happened.
"""

from dataclasses import dataclass
from datetime import datetime

GRANTED = "GRANTED"
DENIED = "DENIED"
LOCKOUT = "LOCKOUT"
UNLOCKED = "UNLOCKED"


@dataclass
class Record:
    number: int
    time: str        # HH:MM:SS
    result: str      # one of the constants above
    detail: str


class AuthHistory:
    def __init__(self, now=datetime.now):
        self._records = []
        self._now = now

    def add(self, result, detail=""):
        record = Record(
            number=len(self._records) + 1,
            time=self._now().strftime("%H:%M:%S"),
            result=result,
            detail=detail,
        )
        self._records.append(record)
        return record

    def recent(self, count=None):
        """Newest `count` records, oldest first (all records if count is None)."""
        if count is None:
            return list(self._records)
        return list(self._records[-count:])

    def count(self, result):
        return sum(1 for r in self._records if r.result == result)

    def __len__(self):
        return len(self._records)
