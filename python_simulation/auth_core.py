"""Hardware-independent authentication logic.

No printing, no sleeping, no input: it only tracks state. The clock is
injectable so the lockout can be unit-tested without waiting 30 seconds.
This is the Python twin of firmware/auth.c.
"""

import hmac
import time
from enum import Enum, auto

import config


class Event(Enum):
    NONE = auto()      # key ignored (or system locked)
    DIGIT = auto()     # digit accepted, still collecting
    CLEARED = auto()   # entry cleared with '*'
    GRANTED = auto()   # correct password
    DENIED = auto()    # wrong password


class AuthSystem:
    def __init__(
        self,
        password=config.DEFAULT_PASSWORD,
        password_length=config.PASSWORD_LENGTH,
        max_attempts=config.MAX_ATTEMPTS,
        lockout_seconds=config.LOCKOUT_SECONDS,
        clock=time.monotonic,
    ):
        if len(password) != password_length or not password.isdigit():
            raise ValueError(f"password must be exactly {password_length} digits")
        self._password = password
        self.password_length = password_length
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._clock = clock

        self.buffer = ""
        self.failed_attempts = 0
        self._lockout_end = None  # None = not locked

    # ---- state queries -------------------------------------------------
    @property
    def locked(self):
        """True while the lockout period is running."""
        if self._lockout_end is None:
            return False
        if self._clock() >= self._lockout_end:
            self._end_lockout()
            return False
        return True

    def lockout_remaining(self):
        """Whole seconds left in the lockout (0 when not locked)."""
        if not self.locked:
            return 0
        remaining = self._lockout_end - self._clock()
        return max(0, int(remaining) + (1 if remaining % 1 else 0))

    # ---- actions ---------------------------------------------------------
    def press(self, key):
        """Feed one keypad key; returns an Event."""
        if self.locked:
            return Event.NONE  # keypad is dead during lockout

        if key == config.CLEAR_KEY:
            self.buffer = ""
            return Event.CLEARED

        if not (len(key) == 1 and key.isdigit()):
            return Event.NONE  # A-D and '#' are unused

        self.buffer += key
        if len(self.buffer) < self.password_length:
            return Event.DIGIT

        # full password entered -> compare (constant-time) and reset buffer
        entered, self.buffer = self.buffer, ""
        if hmac.compare_digest(entered, self._password):
            self.failed_attempts = 0
            return Event.GRANTED

        self.failed_attempts += 1
        if self.failed_attempts >= self.max_attempts:
            self._lockout_end = self._clock() + self.lockout_seconds
        return Event.DENIED

    def _end_lockout(self):
        self._lockout_end = None
        self.failed_attempts = 0
        self.buffer = ""
