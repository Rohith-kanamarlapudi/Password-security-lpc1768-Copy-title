"""Tests for the virtual board (LCD / LED / buzzer rules) and the history log."""

import unittest

import ui
from history import AuthHistory, DENIED, GRANTED, LOCKOUT
from virtual_board import VirtualBoard


class BoardTests(unittest.TestCase):
    def test_buzzer_sounds_only_when_denied(self):
        board = VirtualBoard()
        board.signal_denied()
        self.assertTrue(board.buzzer)
        self.assertTrue(board.red_led)
        self.assertFalse(board.green_led)

        board.signal_granted()
        self.assertFalse(board.buzzer)          # off again on success
        self.assertTrue(board.green_led)
        self.assertFalse(board.red_led)

        board.signal_locked()
        self.assertFalse(board.buzzer)
        self.assertTrue(board.red_led)

        board.signal_idle()
        self.assertFalse(board.buzzer)
        self.assertFalse(board.green_led or board.red_led)

    def test_granted_switches_a_sounding_buzzer_off(self):
        board = VirtualBoard()
        board.buzzer = True
        board.signal_granted()
        self.assertFalse(board.buzzer)

    def test_lcd_is_limited_to_16_characters(self):
        board = VirtualBoard()
        board.lcd("X" * 40, "Y" * 40)
        self.assertEqual(len(board.line1), 16)
        self.assertEqual(len(board.line2), 16)

    def test_panel_lines_have_equal_width(self):
        board = VirtualBoard()
        board.lcd("Access Denied", "Attempt 1/3")
        board.signal_denied()
        for ansi in (True, False):
            ui.USE_ANSI = ansi
            widths = {ui.visible_len(line) for line in board.panel()}
            self.assertEqual(widths, {ui.WIDTH})
        ui.USE_ANSI = False


class HistoryTests(unittest.TestCase):
    def test_records_are_numbered_and_counted(self):
        log = AuthHistory()
        log.add(DENIED, "Attempt 1 of 3")
        log.add(GRANTED)
        log.add(LOCKOUT)
        self.assertEqual(len(log), 3)
        self.assertEqual([r.number for r in log.recent()], [1, 2, 3])
        self.assertEqual(log.count(DENIED), 1)

    def test_recent_returns_newest_in_order(self):
        log = AuthHistory()
        for _ in range(15):
            log.add(DENIED)
        recent = log.recent(10)
        self.assertEqual(len(recent), 10)
        self.assertEqual(recent[0].number, 6)
        self.assertEqual(recent[-1].number, 15)


if __name__ == "__main__":
    unittest.main()
