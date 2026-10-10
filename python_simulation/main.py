"""Laptop demo of the LPC1768 password security system (software simulation).

Run:
    python main.py                 # menu-driven demo, password 1234, 30 s lockout
    python main.py --fast          # 5 s lockout and quicker animations
    python main.py --demo          # automatic walkthrough of every feature
    python main.py --plain         # no colours / box characters (very old terminals)
    python main.py --password 4821 --attempts 3 --lockout 30

Tip: maximise the VS Code terminal panel so the whole screen fits.
Nothing here is connected to real hardware: the LCD, LEDs and buzzer are drawn
as text. The real hardware version is the C code in ../firmware.
"""

import argparse
import getpass
import sys
import time

import config
import history
import screens
import ui
from auth_core import AuthSystem, Event
from history import AuthHistory
from virtual_board import VirtualBoard


class App:
    """Everything the screens need, in one place."""

    def __init__(self, system, password):
        self.system = system
        self.password = password        # only used by the automatic demo
        self.board = VirtualBoard()
        self.history = AuthHistory()
        self.note = ""                  # message shown at the bottom of a screen


# --------------------------------------------------------------------------
# input helpers
# --------------------------------------------------------------------------
def flush_input():
    """Drop keys typed while the keypad was 'dead' during lockout."""
    try:
        import msvcrt  # Windows

        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        try:
            import termios

            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except Exception:
            pass


def read_hidden(prompt):
    """Read a line without showing it (nothing to hide when input is piped)."""
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    return input(prompt)


def wait_for_enter(prompt):
    try:
        input(prompt)
    except (EOFError, KeyboardInterrupt):
        pass


# --------------------------------------------------------------------------
# start-up
# --------------------------------------------------------------------------
def startup(app):
    total = len(screens.BOOT_STEPS)
    if ui.USE_ANSI:
        for done in range(total + 1):
            ui.show(screens.startup_screen(app, done), fresh=(done == 0))
            ui.wait(0.3)
        ui.wait(0.8)
    else:
        ui.show(screens.startup_screen(app, total), fresh=True)


# --------------------------------------------------------------------------
# one authentication attempt
# --------------------------------------------------------------------------
def process_keys(app, raw):
    """Press the typed keys one at a time, like a real keypad.

    Returns (event, ignored, partial): the GRANTED / DENIED event if a full
    password was entered (else None), how many keys were ignored, and how many
    digits were left over from an unfinished entry.
    """
    system, board = app.system, app.board
    ignored = 0
    for index, key in enumerate(raw):
        event = system.press(key)
        if event in (Event.DIGIT, Event.CLEARED):
            board.lcd("Enter Password", "*" * len(system.buffer))
            if ui.USE_ANSI:
                ui.show(screens.auth_screen(app))
                ui.wait(0.15)
        elif event is Event.NONE:
            ignored += 1
        else:                                   # GRANTED or DENIED
            return event, ignored + len(raw) - index - 1, 0
    partial = len(system.buffer)
    system.clear_entry()                        # an unfinished entry is never kept
    return None, ignored, partial


def show_granted(app):
    app.history.add(history.GRANTED, "Failed-attempt counter reset")
    app.board.signal_granted()                  # green LED on, buzzer OFF
    app.board.lcd("Access Granted", "Welcome!")
    ui.show(screens.result_screen(app, "granted"))
    ui.wait(config.RESULT_PAUSE_SECONDS)


def show_denied(app):
    system = app.system
    app.history.add(history.DENIED, f"Attempt {system.failed_attempts} of {system.max_attempts}")
    app.board.signal_denied()                   # red LED on, buzzer ON
    app.board.lcd("Access Denied", f"Attempt {system.failed_attempts}/{system.max_attempts}")
    ui.show(screens.result_screen(app, "denied"))
    ui.wait(config.RESULT_PAUSE_SECONDS)
    if system.locked:                           # buzzer goes off either way
        app.board.signal_locked()
    else:
        app.board.signal_idle()


def run_lockout(app):
    """Blocks until the lockout ends, redrawing the countdown every second."""
    system, board = app.system, app.board
    app.history.add(history.LOCKOUT, f"Keypad disabled for {system.lockout_seconds} s")
    board.signal_locked()
    system.restart_lockout()                    # full period starts after the "Denied" message
    last, first = None, True
    while system.locked:
        remaining = system.lockout_remaining()
        if remaining != last:
            last = remaining
            board.lcd("System Locked", f"Wait {remaining:>2} sec")
            # with colours off each frame is printed, so only show every 5 s
            if ui.USE_ANSI or first or remaining % 5 == 0:
                ui.show(screens.lockout_screen(app, remaining), fresh=first)
            first = False
        time.sleep(0.1)                         # real time: the lockout is never skipped
    app.history.add(history.UNLOCKED, "Keypad re-enabled, attempts reset")
    board.signal_idle()
    board.lcd("Lockout over", "Try again")
    saved, app.note = app.note, "Lockout over - the keypad works again."
    ui.show(screens.auth_screen(app), fresh=True)
    ui.wait(1.5)
    app.note = saved
    flush_input()


def handle_entry(app, raw):
    """Type `raw` on the virtual keypad and carry out the result.

    Returns (event, note) where note is a hint for the next screen.
    """
    system, board = app.system, app.board
    event, ignored, partial = process_keys(app, raw)
    note = ""
    if event is not None:
        board.lcd("Checking...", "")
        if ui.USE_ANSI:
            saved, app.note = app.note, "Checking password..."
            ui.show(screens.auth_screen(app))
            app.note = saved
            ui.wait(0.5)
    if event is Event.GRANTED:
        show_granted(app)
    elif event is Event.DENIED:
        show_denied(app)
        if system.locked:
            run_lockout(app)
    elif partial:
        note = f"Only {partial} of {system.password_length} digits entered - entry cleared (not counted)."
    if ignored:
        note = f"{ignored} unused or extra key(s) ignored."
    return event, note


# --------------------------------------------------------------------------
# menu actions
# --------------------------------------------------------------------------
def authenticate(app):
    note = ""
    while True:
        app.board.signal_idle()
        app.board.lcd("Enter Password", "")
        app.note = note
        ui.show(screens.auth_screen(app), fresh=True)
        app.note = ""
        try:
            raw = read_hidden("  Password > ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not raw:
            return                              # ENTER alone: back to the menu
        event, note = handle_entry(app, raw)
        if event is Event.GRANTED:
            return


def show_history(app, prompt="  Press Enter to return to the menu "):
    ui.show(screens.history_screen(app), fresh=True)
    wait_for_enter(prompt)


def show_info(app):
    ui.show(screens.info_screen(app), fresh=True)
    wait_for_enter("  Press Enter to return to the menu ")


def run_demo(app):
    """Automatic walkthrough: wrong, typo + wrong, correct, lockout, correct."""
    system = app.system
    wrong = "0000" if app.password != "0000" else "1111"
    steps = [
        ("Step 1/5: a wrong password", [wrong]),
        ("Step 2/5: typo cleared with '*', then a wrong password", ["99*" + wrong]),
        ("Step 3/5: the correct password (counter resets)", [app.password]),
        (f"Step 4/5: {system.max_attempts} wrong passwords in a row", [wrong] * system.max_attempts),
        ("Step 5/5: the correct password after the lockout", [app.password]),
    ]
    system.reset()
    for title, attempts in steps:
        app.note = title
        for raw in attempts:
            app.board.signal_idle()
            app.board.lcd("Enter Password", "")
            ui.show(screens.auth_screen(app), fresh=True)
            ui.wait(1.0)
            handle_entry(app, raw)
    app.note = ""
    app.board.signal_idle()


def menu_loop(app):
    note = ""
    while True:
        app.board.signal_idle()
        app.board.lcd("Enter Password", "")
        app.note = note
        ui.show(screens.menu_screen(app), fresh=True)
        app.note = ""
        note = ""
        try:
            choice = input("  Select an option > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if choice == "1":
            authenticate(app)
        elif choice == "2":
            show_history(app)
        elif choice == "3":
            show_info(app)
        elif choice == "4":
            run_demo(app)
            show_history(app)
        elif choice in ("0", "q", "quit", "exit"):
            return
        else:
            note = "Please choose 1, 2, 3, 4 or 0."


# --------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="LPC1768 password security system (simulation)")
    p.add_argument("--password", default=config.DEFAULT_PASSWORD, help="4-digit password")
    p.add_argument("--attempts", type=int, default=config.MAX_ATTEMPTS)
    p.add_argument("--lockout", type=int, default=None, help="lockout seconds (default 30)")
    p.add_argument("--fast", action="store_true", help="5 s lockout and quicker animations")
    p.add_argument("--demo", action="store_true", help="run the automatic walkthrough, then exit")
    p.add_argument("--plain", action="store_true", help="no colours or box-drawing characters")
    return p.parse_args()


def main():
    args = parse_args()
    ui.setup(plain=args.plain, fast=args.fast)
    lockout = args.lockout
    if lockout is None:
        lockout = 5 if args.fast else config.LOCKOUT_SECONDS

    try:
        system = AuthSystem(
            password=args.password,
            max_attempts=args.attempts,
            lockout_seconds=lockout,
        )
    except ValueError as err:
        sys.exit(f"Error: {err}")

    app = App(system, args.password)
    try:
        startup(app)
        if args.demo:
            run_demo(app)
            show_history(app, prompt="  Demo finished. Press Enter to exit ")
        else:
            menu_loop(app)
    except KeyboardInterrupt:
        pass
    ui.show(screens.goodbye_screen(app), fresh=True)
    ui.reset_style()


if __name__ == "__main__":
    main()
