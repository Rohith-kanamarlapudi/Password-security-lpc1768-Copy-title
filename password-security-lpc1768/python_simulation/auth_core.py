"""Hardware-independent authentication logic.

No printing, no sleeping, no input: it only tracks state. The clock is
injectable so the lockout can be unit-tested without waiting 30 seconds.
This is the Python twin of firmware/auth.c.
"""

import hmac
import math
import time
from enum import Enum, auto

import config

DIGITS = "0123456789"


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
        if not (password.isascii() and password.isdigit() and len(password) == password_length):
            raise ValueError(f"password must be exactly {password_length} digits (0-9)")
        if max_attempts < 1:
            raise ValueError("attempt limit must be at least 1")
        if lockout_seconds < 1:
            raise ValueError("lockout time must be at least 1 second")
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
        # round up, ignoring tiny floating-point noise (30.0000000001 counts as 30);
        # while still locked there is always at least 1 second left to show
        return max(1, math.ceil(remaining - 1e-6))

    # ---- actions ---------------------------------------------------------
    def press(self, key):
        """Feed one keypad key; returns an Event."""
        if self.locked:
            return Event.NONE  # keypad is dead during lockout

        if key == config.CLEAR_KEY:
            self.buffer = ""
            return Event.CLEARED

        # Only plain 0-9 count. (str.isdigit() also accepts characters such as
        # '²', which would crash the password comparison below.)
        if not (len(key) == 1 and key in DIGITS):
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

    def restart_lockout(self):
        """Start the lockout period again from now (does nothing if not locked).

        The interface calls this after the "Access Denied" message has been
        shown, so the full period counts down on screen - the firmware also
        starts its lockout timer after that message.
        """
        if self.locked:
            self._lockout_end = self._clock() + self.lockout_seconds

    def clear_entry(self):
        """Throw away digits typed so far (an unfinished entry is never kept)."""
        self.buffer = ""

    def reset(self):
        """Back to the power-on state: no digits, no failures, not locked."""
        self.buffer = ""
        self.failed_attempts = 0
        self._lockout_end = None

    def _end_lockout(self):
        self._lockout_end = None
        self.failed_attempts = 0
        self.buffer = ""
