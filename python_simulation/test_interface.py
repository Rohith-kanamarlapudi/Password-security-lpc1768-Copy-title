"""End-to-end tests of the interface flow (no real waiting, no real terminal).

The screen drawing, pauses and sleeping are replaced by recorders so the
tests run instantly but still follow the real code path of main.py.
"""

import unittest
from unittest import mock

import config
import history
import main
import screens
import ui
from auth_core import AuthSystem, Event
from test_auth import FakeClock

PASSWORD = "7391"
WRONG = "0000"


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        system = AuthSystem(password=PASSWORD, max_attempts=3, lockout_seconds=30, clock=self.clock)
        self.app = main.App(system, PASSWORD)
        self.frames = []            # board state at every screen that was drawn
        self.drawn = []             # the text of every screen that was drawn

        def record(lines, fresh=False):
            b = self.app.board
            self.frames.append(
                {"line1": b.line1, "buzzer": b.buzzer, "green": b.green_led, "red": b.red_led,
                 "time": self.clock()}
            )
            self.drawn.append("\n".join(lines))

        patches = [
            mock.patch.object(ui, "show", record),
            # pauses take (fake) time, just like real ones
            mock.patch.object(ui, "wait", lambda s: self.clock.advance(s * ui.SPEED)),
            mock.patch.object(main.time, "sleep", lambda s: self.clock.advance(s)),
            mock.patch.object(main, "flush_input", lambda: None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        ui.USE_ANSI = True          # exercise the animated path too
        ui.USE_UNICODE = True
        self.addCleanup(setattr, ui, "USE_ANSI", False)

    # ---- the buzzer rule -------------------------------------------------
    def test_buzzer_sounds_only_on_failed_attempt(self):
        main.handle_entry(self.app, WRONG)
        main.handle_entry(self.app, PASSWORD)

        denied = [f for f in self.frames if f["line1"] == "Access Denied"]
        granted = [f for f in self.frames if f["line1"] == "Access Granted"]
        self.assertTrue(denied and granted)
        self.assertTrue(all(f["buzzer"] and f["red"] for f in denied))
        self.assertTrue(all(not f["buzzer"] and f["green"] and not f["red"] for f in granted))
        # on every other screen (typing, checking, idle) the buzzer is off
        others = [f for f in self.frames if f["line1"] != "Access Denied"]
        self.assertTrue(all(not f["buzzer"] for f in others))
        self.assertFalse(self.app.board.buzzer)

    def test_buzzer_off_during_lockout_and_afterwards(self):
        for _ in range(3):
            main.handle_entry(self.app, WRONG)
        locked = [f for f in self.frames if f["line1"] == "System Locked"]
        self.assertTrue(locked)
        self.assertTrue(all(f["red"] and not f["buzzer"] for f in locked))
        self.assertFalse(self.app.board.buzzer)

    # ---- attempt limit and lockout ----------------------------------------
    def test_three_failures_lock_for_30_seconds_then_resume(self):
        for _ in range(3):
            event, _note = main.handle_entry(self.app, WRONG)
            self.assertIs(event, Event.DENIED)
        # The on-screen countdown starts at a full 00:30 (the 'Access Denied'
        # message does not use up part of it) and runs for 30 seconds.
        locked = [i for i, f in enumerate(self.frames) if f["line1"] == "System Locked"]
        self.assertIn("00:30", self.drawn[locked[0]])
        self.assertIn("00:01", self.drawn[locked[-1]])
        over = next(f for f in self.frames if f["line1"] == "Lockout over")
        lockout_time = over["time"] - self.frames[locked[0]]["time"]
        self.assertGreaterEqual(lockout_time, 30)
        self.assertLess(lockout_time, 30.5)
        self.assertFalse(self.app.system.locked)
        self.assertEqual(self.app.system.failed_attempts, 0)
        log = self.app.history
        self.assertEqual((log.count(history.DENIED), log.count(history.LOCKOUT), log.count(history.UNLOCKED)), (3, 1, 1))
        event, _note = main.handle_entry(self.app, PASSWORD)
        self.assertIs(event, Event.GRANTED)

    def test_no_lockout_after_two_failures(self):
        main.handle_entry(self.app, WRONG)
        main.handle_entry(self.app, WRONG)
        self.assertEqual(self.app.history.count(history.LOCKOUT), 0)
        self.assertEqual(self.app.system.failed_attempts, 2)

    def test_denied_screen_shows_live_counter(self):
        main.handle_entry(self.app, WRONG)
        self.assertIn("Attempt 1 of 3", self.drawn[-1])
        self.assertIn("1/3", self.drawn[-1])

    # ---- input handling ---------------------------------------------------
    def test_unfinished_entry_is_cleared_and_not_counted(self):
        event, note = main.handle_entry(self.app, "73")
        self.assertIsNone(event)
        self.assertIn("Only 2 of 4", note)
        self.assertEqual(self.app.system.buffer, "")
        self.assertEqual(self.app.system.failed_attempts, 0)
        # the leftover '73' must not combine with the next entry
        event, _ = main.handle_entry(self.app, "91")
        self.assertIsNone(event)

    def test_odd_characters_do_not_crash(self):
        event, note = main.handle_entry(self.app, "²²²²")
        self.assertIsNone(event)
        self.assertIn("ignored", note)
        self.assertEqual(self.app.system.failed_attempts, 0)

    def test_extra_keys_after_fourth_digit_ignored(self):
        event, note = main.handle_entry(self.app, PASSWORD + "99")
        self.assertIs(event, Event.GRANTED)
        self.assertIn("2", note)

    # ---- privacy and layout -----------------------------------------------
    def test_password_never_appears_on_screen(self):
        main.handle_entry(self.app, WRONG)
        main.handle_entry(self.app, PASSWORD)
        self.app.note = ""
        screen_text = "\n".join(self.drawn) + "\n".join(
            "\n".join(fn(self.app)) for fn in (screens.menu_screen, screens.history_screen, screens.info_screen)
        )
        self.assertNotIn(PASSWORD, screen_text)

    def test_every_screen_line_is_aligned(self):
        for _ in range(12):                              # enough rows to trigger "showing last N"
            main.handle_entry(self.app, WRONG if _ % 4 else PASSWORD)
        self.app.note = "A short note for the bottom line."
        for ansi in (True, False):
            for unicode_ok in (True, False):
                ui.USE_ANSI, ui.USE_UNICODE = ansi, unicode_ok
                built = {
                    "menu": screens.menu_screen(self.app),
                    "auth": screens.auth_screen(self.app),
                    "granted": screens.result_screen(self.app, "granted"),
                    "denied": screens.result_screen(self.app, "denied"),
                    "lockout": screens.lockout_screen(self.app, 17),
                    "history": screens.history_screen(self.app),
                    "info": screens.info_screen(self.app),
                    "goodbye": screens.goodbye_screen(self.app),
                }
                for done in range(len(screens.BOOT_STEPS) + 1):
                    built[f"startup{done}"] = screens.startup_screen(self.app, done)
                for name, lines in built.items():
                    for line in lines:
                        width = ui.visible_len(line)
                        self.assertIn(
                            width, (0, ui.WIDTH),
                            f"{name} (ansi={ansi}, unicode={unicode_ok}): width {width}: {line!r}",
                        )
        ui.USE_ANSI, ui.USE_UNICODE = True, True


if __name__ == "__main__":
    unittest.main()
