"""Shared settings for the simulation.

These values mirror firmware/config.h so both versions behave the same.
"""

DEFAULT_PASSWORD = "1234"   # 4-digit password (change here and in firmware/config.h)
PASSWORD_LENGTH = 4
MAX_ATTEMPTS = 3            # consecutive wrong attempts before lockout
LOCKOUT_SECONDS = 30        # lockout duration
RESULT_PAUSE_SECONDS = 2.0  # how long "Access Granted/Denied" stays on screen

# Keys on the 4x4 matrix keypad (same layout assumed in firmware/keypad.c)
KEYPAD_LAYOUT = (
    ("1", "2", "3", "A"),
    ("4", "5", "6", "B"),
    ("7", "8", "9", "C"),
    ("*", "0", "#", "D"),
)
CLEAR_KEY = "*"             # clears the digits entered so far
