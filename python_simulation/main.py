"""Laptop demo of the LPC1768 password security system.

Run:
    python main.py                 # interactive, password 1234, 30 s lockout
    python main.py --fast          # 5 s lockout, short pauses (quick demo)
    python main.py --demo          # scripted run showing every feature
    python main.py --password 4821 --attempts 3 --lockout 30

Type keypad keys (0-9, '*' clears) at the "Keypad>" prompt, then press Enter.
You may type several keys at once, e.g. 1234. Type q to quit.
"""

import argparse
import sys
import time

import config
from auth_core import AuthSystem, Event
from virtual_board import VirtualBoard


# --------------------------------------------------------------------------
# helpers
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


def show_entry(board, system):
    board.leds()
    board.buzzer = False
    board.lcd("Enter Password", "*" * len(system.buffer))
    board.render()


def do_granted(board, pause):
    board.leds(green=True)
    board.buzzer = True            # single short beep
    board.lcd("Access Granted", "Welcome!")
    board.render()
    time.sleep(min(0.3, pause))
    board.buzzer = False
    time.sleep(pause)


def do_denied(board, system, pause):
    board.leds(red=True)
    board.buzzer = True
    board.lcd("Access Denied", f"Attempt {system.failed_attempts}/{system.max_attempts}")
    board.render()
    time.sleep(pause)
    board.buzzer = False


def do_lockout(board, system):
    """Blocks until the lockout expires, updating the countdown each second."""
    last = None
    while system.locked:
        remaining = system.lockout_remaining()
        if remaining != last:
            board.leds(red=True)
            board.buzzer = False
            board.lcd("System Locked", f"Wait {remaining:>2} sec")
            board.render()
            last = remaining
        time.sleep(0.1)
    board.lcd("Lockout over", "Try again")
    board.leds()
    board.render()
    time.sleep(1)


def handle_key(key, board, system, pause):
    """Process one key. Returns True if a full attempt just finished."""
    event = system.press(key)
    if event is Event.GRANTED:
        do_granted(board, pause)
        return True
    if event is Event.DENIED:
        do_denied(board, system, pause)
        if system.locked:
            do_lockout(board, system)
        return True
    if event in (Event.DIGIT, Event.CLEARED):
        show_entry(board, system)
    return False


# --------------------------------------------------------------------------
# modes
# --------------------------------------------------------------------------
def interactive(board, system, pause):
    print(__doc__)
    show_entry(board, system)
    while True:
        try:
            raw = input("Keypad> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        if raw.lower() in ("q", "quit", "exit"):
            print("Bye.")
            return
        for key in raw:
            if handle_key(key, board, system, pause):
                flush_input()
                show_entry(board, system)
                break  # discard leftover keys after a finished attempt


def scripted_demo(board, system, pause, password):
    wrong = "0000"
    steps = [
        ("Wrong password (attempt 1)", wrong),
        ("Typo, cleared with '*' then wrong again (attempt 2)", "99*" + wrong),
        ("Correct password -> access granted, counter resets", password),
        ("Wrong x3 -> lockout", wrong + wrong + wrong),
        ("(After lockout) correct password", password),
    ]
    show_entry(board, system)
    for title, keys in steps:
        print(f"=== {title}: pressing {keys!r}")
        for key in keys:
            print(f"--- key {key!r}")
            if handle_key(key, board, system, pause):
                show_entry(board, system)
    print("Demo finished.")


# --------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="LPC1768 password security system (simulation)")
    p.add_argument("--password", default=config.DEFAULT_PASSWORD, help="4-digit password")
    p.add_argument("--attempts", type=int, default=config.MAX_ATTEMPTS)
    p.add_argument("--lockout", type=int, default=None, help="lockout seconds (default 30)")
    p.add_argument("--fast", action="store_true", help="5 s lockout and short pauses")
    p.add_argument("--demo", action="store_true", help="run a scripted walkthrough")
    return p.parse_args()


def main():
    args = parse_args()
    lockout = args.lockout
    if lockout is None:
        lockout = 5 if args.fast else config.LOCKOUT_SECONDS
    pause = 0.5 if (args.fast or args.demo) else config.RESULT_PAUSE_SECONDS

    try:
        system = AuthSystem(
            password=args.password,
            max_attempts=args.attempts,
            lockout_seconds=lockout,
        )
    except ValueError as err:
        sys.exit(f"Error: {err}")

    board = VirtualBoard()
    if args.demo:
        scripted_demo(board, system, pause, args.password)
    else:
        interactive(board, system, pause)


if __name__ == "__main__":
    main()
