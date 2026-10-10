"""Builds each screen of the terminal interface as a list of text lines.

Screens only *describe* what to draw; main.py decides when to draw them.
Every screen ends with one "note" line (app.note) for hints and messages.
"""

import config
import history
import ui

INNER = ui.WIDTH - 4           # usable width inside a box


# ---------------------------------------------------------------- shared parts
def banner():
    return ui.box(
        [
            ui.center(ui.paint(config.PROJECT_TITLE, "bold", "white"), INNER),
            ui.center(ui.paint(config.PROJECT_SUBTITLE, "cyan"), INNER),
        ],
        color="cyan",
        double=True,
    )


def attempt_dots(used, limit):
    if limit > 6:
        return ""
    dots = [
        ui.paint(ui.g("led_on"), "red") if i < used else ui.paint(ui.g("led_off"), "gray")
        for i in range(limit)
    ]
    return " ".join(dots) + " "


def status_bar(app):
    s = app.system
    state = ui.badge("LOCKED", "bg_red") if s.locked else ui.badge("READY", "bg_green")
    parts = [
        f"SYSTEM {state}",
        f"FAILED ATTEMPTS {attempt_dots(s.failed_attempts, s.max_attempts)}{s.failed_attempts}/{s.max_attempts}",
        f"LOCKOUT {s.lockout_seconds} s",
    ]
    return ui.center("   ".join(parts))


def note_line(app):
    return ui.center(ui.paint(app.note, "yellow")) if app.note else ""


def top(app):
    """Banner + status bar + simulated board: the top of every main screen."""
    return [*banner(), status_bar(app), "", *app.board.panel(), ""]


# ---------------------------------------------------------------- start-up
BOOT_STEPS = (
    ("Virtual 4x4 matrix keypad", "ready"),
    ("Virtual 16x2 LCD display", "ready"),
    ("Virtual green / red LEDs", "ready"),
    ("Virtual buzzer", "ready"),
    ("Lockout timer", None),             # value filled in from the settings
    ("Authentication engine", "ready"),
)


def startup_screen(app, done):
    """`done` = number of boot steps finished so far (0 .. len(BOOT_STEPS))."""
    team = ui.box(
        [ui.center(ui.paint(name, "white"), INNER) for name in config.TEAM],
        title="MINI PROJECT TEAM",
        color="magenta",
    )
    log = []
    for i, (name, value) in enumerate(BOOT_STEPS):
        if i < done:
            value = value or f"{app.system.lockout_seconds} s"
            log.append(ui.paint("[ OK ]", "bold", "green") + " " + ui.dotted(name, value, INNER - 7))
        else:
            log.append("")
    log.append("")
    log.append(ui.center(ui.bar(done / len(BOOT_STEPS), 40, "cyan"), INNER))
    boot = ui.box(log, title="STARTING UP (simulated hardware)", color="blue")

    ready = ""
    if done == len(BOOT_STEPS):
        ready = ui.center(ui.paint("System ready - no real hardware is connected", "bold", "green"))
    return [*banner(), "", *team, "", *boot, ready]


# ---------------------------------------------------------------- main menu
def menu_screen(app):
    items = [
        "[1]  Enter password (authenticate)",
        "[2]  Authentication history",
        "[3]  System information",
        "[4]  Run automatic demo",
        "[0]  Exit",
    ]
    colored = [ui.paint(line[:3], "bold", "cyan") + line[3:] for line in items]
    menu = ui.box(["", *colored], title="MAIN MENU", color="cyan")
    return [*top(app), *menu, note_line(app)]


# ---------------------------------------------------------------- authentication
def keypad_panel():
    n = config.PASSWORD_LENGTH
    grid = []
    for row in config.KEYPAD_LAYOUT:
        keys = []
        for key in row:
            if key == config.CLEAR_KEY:
                keys.append(ui.paint(key, "bold", "yellow"))
            elif key.isdigit():
                keys.append(ui.paint(key, "bold", "cyan"))
            else:
                keys.append(ui.paint(key, "gray"))      # unused keys
        grid.append("  ".join(keys))
    help_text = [
        f"Type the {n}-digit password, press ENTER",
        f"Your typing is hidden; the LCD shows {'*' * n}",
        ui.paint(config.CLEAR_KEY, "bold", "yellow") + "  clears the digits typed so far",
        "ENTER alone goes back to the menu",
    ]
    lines = [f"  {ui.pad(k, 10)}    {t}" for k, t in zip(grid, help_text)]
    return ui.box(lines, title="KEYPAD GUIDE (4x4 matrix)", color="cyan")


def auth_screen(app):
    return [*top(app), *keypad_panel(), note_line(app)]


def result_screen(app, kind):
    """kind is 'granted' or 'denied'."""
    s = app.system
    if kind == "granted":
        bg, symbol, text, plain = "bg_green", ui.g("ok"), "ACCESS GRANTED", "*"
        info = [
            ui.paint("Correct password. Welcome!", "green"),
            f"Failed-attempt counter reset to 0/{s.max_attempts}.",
        ]
    else:
        bg, symbol, text, plain = "bg_red", ui.g("bad"), "ACCESS DENIED", "!"
        left = s.max_attempts - s.failed_attempts
        if s.locked:
            second = ui.paint(f"No attempts left - locking the system for {s.lockout_seconds} s.", "bold", "red")
        else:
            second = f"{left} attempt(s) left before lockout."
        info = [
            ui.paint(f"Wrong password. Attempt {s.failed_attempts} of {s.max_attempts}.", "red"),
            second,
        ]
    msg = ui.paint(ui.center(f"{symbol}   {text}   {symbol}"), "bold", "white", bg) if ui.USE_ANSI \
        else ui.center(f"{symbol}   {text}   {symbol}")
    banner_rows = [ui.solid_row(bg, plain), msg, ui.solid_row(bg, plain)]
    return [*top(app), *banner_rows, "", *[ui.center(i) for i in info], note_line(app)]


def lockout_screen(app, remaining):
    s = app.system
    minutes, seconds = divmod(remaining, 60)
    lines = [
        "",
        ui.center(ui.paint("KEYPAD DISABLED - ALL KEY PRESSES ARE IGNORED", "bold", "red"), INNER),
        "",
        ui.center(ui.paint(f"{minutes:02d}:{seconds:02d}", "bold", "white")
                  + "  remaining", INNER),
        ui.center(ui.bar(remaining / s.lockout_seconds, 50, "red"), INNER),
        "",
    ]
    box = ui.box(lines, title="SYSTEM LOCKED", color="red")
    return [*top(app), *box, note_line(app)]


# ---------------------------------------------------------------- history
RESULT_COLORS = {
    history.GRANTED: "green",
    history.DENIED: "red",
    history.LOCKOUT: "yellow",
    history.UNLOCKED: "cyan",
}


def history_screen(app):
    log = app.history
    rows = log.recent(config.HISTORY_SHOWN)
    if rows:
        lines = [ui.paint(f"{'#':>3}  {'TIME':<8}  {'RESULT':<9}  DETAIL", "bold", "white")]
        for r in rows:
            result = ui.paint(r.result, "bold", RESULT_COLORS[r.result])
            lines.append(f"{r.number:>3}  {r.time:<8}  {ui.pad(result, 9)}  {r.detail}")
    else:
        lines = ["", ui.center(ui.paint("No authentication attempts yet.", "dim"), INNER)]
    shown = f"showing last {len(rows)} of {len(log)}" if len(log) > len(rows) else "this session"
    summary = (
        f"Granted: {log.count(history.GRANTED)}   Denied: {log.count(history.DENIED)}"
        f"   Lockouts: {log.count(history.LOCKOUT)}"
    )
    panel = ui.box([*lines, "", ui.paint(summary, "cyan")], title=f"AUTHENTICATION HISTORY ({shown})", color="cyan")
    return [*banner(), status_bar(app), "", *panel, note_line(app)]


# ---------------------------------------------------------------- information
def info_screen(app):
    s = app.system
    w = INNER - 2
    settings = ui.box(
        [
            ui.dotted("Password length", f"{s.password_length} digits (hidden)", w),
            ui.dotted("Failed-attempt limit", str(s.max_attempts), w),
            ui.dotted("Lockout duration", f"{s.lockout_seconds} seconds", w),
            ui.dotted("Keypad during lockout", "disabled", w),
        ],
        title="SETTINGS",
        color="cyan",
    )
    pins = ui.box(
        [
            ui.dotted("Keypad rows", "P2.10 - P2.13", w),
            ui.dotted("Keypad columns", "P1.23 - P1.26", w),
            ui.dotted("LCD data D4 - D7", "P0.23 - P0.26", w),
            ui.dotted("LCD RS / EN", "P0.27 / P0.28", w),
            ui.dotted("Green LED / Red LED", "P0.4 / P0.5", w),
            ui.dotted("Buzzer", "On-board", w),
        ],
        title="TARGET HARDWARE MAP (LPC1768 firmware)",
        color="blue",
    )
    note = ui.center(ui.paint("Software simulation only - it never talks to a real board.", "dim"))
    return [*banner(), status_bar(app), "", *settings, *pins, note, note_line(app)]


# ---------------------------------------------------------------- goodbye
def goodbye_screen(app):
    log = app.history
    lines = [
        ui.dotted("Access granted", str(log.count(history.GRANTED)), INNER - 2),
        ui.dotted("Access denied", str(log.count(history.DENIED)), INNER - 2),
        ui.dotted("Lockouts", str(log.count(history.LOCKOUT)), INNER - 2),
    ]
    panel = ui.box(lines, title="SESSION SUMMARY", color="cyan")
    bye = ui.center(ui.paint("Simulation closed. Goodbye!", "bold", "green"))
    return [*banner(), "", *panel, "", bye, ""]
