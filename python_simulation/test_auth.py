"""Unit tests for the authentication logic. Run: python -m unittest -v"""

import unittest

from auth_core import AuthSystem, Event


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def type_keys(system, keys):
    last = Event.NONE
    for k in keys:
        last = system.press(k)
    return last


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.sys = AuthSystem(
            password="1234", max_attempts=3, lockout_seconds=30, clock=self.clock
        )

    def test_correct_password_granted(self):
        self.assertIs(type_keys(self.sys, "1234"), Event.GRANTED)
        self.assertEqual(self.sys.failed_attempts, 0)

    def test_wrong_password_denied_and_counted(self):
        self.assertIs(type_keys(self.sys, "1111"), Event.DENIED)
        self.assertEqual(self.sys.failed_attempts, 1)
        self.assertFalse(self.sys.locked)

    def test_partial_entry_is_digit_event(self):
        self.assertIs(self.sys.press("1"), Event.DIGIT)

    def test_clear_key_resets_entry(self):
        type_keys(self.sys, "12")
        self.assertIs(self.sys.press("*"), Event.CLEARED)
        self.assertIs(type_keys(self.sys, "1234"), Event.GRANTED)

    def test_unused_keys_ignored(self):
        for k in "ABCD#":
            self.assertIs(self.sys.press(k), Event.NONE)
        self.assertEqual(self.sys.buffer, "")

    def test_lockout_after_three_failures(self):
        for _ in range(3):
            type_keys(self.sys, "0000")
        self.assertTrue(self.sys.locked)
        self.assertEqual(self.sys.lockout_remaining(), 30)

    def test_no_lockout_after_two_failures(self):
        for _ in range(2):
            type_keys(self.sys, "0000")
        self.assertFalse(self.sys.locked)

    def test_keys_ignored_while_locked_even_if_correct(self):
        for _ in range(3):
            type_keys(self.sys, "0000")
        self.assertIs(type_keys(self.sys, "1234"), Event.NONE)
        self.assertTrue(self.sys.locked)

    def test_lockout_lasts_30_seconds(self):
        for _ in range(3):
            type_keys(self.sys, "0000")
        self.clock.advance(29)
        self.assertTrue(self.sys.locked)
        self.assertEqual(self.sys.lockout_remaining(), 1)
        self.clock.advance(1)
        self.assertFalse(self.sys.locked)

    def test_works_again_after_lockout_and_counter_reset(self):
        for _ in range(3):
            type_keys(self.sys, "0000")
        self.clock.advance(30)
        self.assertIs(type_keys(self.sys, "0000"), Event.DENIED)
        self.assertEqual(self.sys.failed_attempts, 1)
        self.assertFalse(self.sys.locked)
        self.assertIs(type_keys(self.sys, "1234"), Event.GRANTED)

    def test_success_resets_failed_counter(self):
        type_keys(self.sys, "0000")
        type_keys(self.sys, "0000")
        type_keys(self.sys, "1234")
        type_keys(self.sys, "0000")
        type_keys(self.sys, "0000")
        self.assertFalse(self.sys.locked)  # only 2 consecutive failures

    def test_invalid_password_config_rejected(self):
        with self.assertRaises(ValueError):
            AuthSystem(password="12")


if __name__ == "__main__":
    unittest.main()
