# Password-Based Security System Using NXP LPC1768

Mini project for the ALS-SDA-ARMCTXM3-01 trainer board (4x4 keypad, 16x2 LCD, LEDs, buzzer).

The project has two independent parts:

| Folder | What it is | Needs hardware? |
|---|---|---|
| `python_simulation/` | Laptop demo of the full behaviour | No |
| `firmware/` | Embedded C for the LPC1768 (Keil uVision) | Yes |

## Behaviour

- Enter a 4-digit password on the keypad. Default password: `1234`.
- Correct: LCD shows **Access Granted**, green LED on, buzzer stays off, attempt counter resets.
- Wrong: LCD shows **Access Denied** and the attempt number, red LED on, **buzzer on**. The buzzer sounds only after a failed attempt.
- After **3 consecutive** wrong attempts: **System Locked** for **30 seconds** with a live countdown. Keys are ignored during lockout. The 30 s start after the "Access Denied" message, as in the firmware.
- After the lockout the system returns to "Enter Password" with the attempt counter reset.
- `*` clears the digits typed so far. `A-D` and `#` are unused.

**Simulation vs firmware, one difference:** the firmware (and the synopsis flowchart) gives a single short beep on Access Granted. The simulation follows the stricter rule above (buzzer only on failure). To make the firmware match, delete the `buzzer_beep(150);` line in `do_access_granted()` in `firmware/main.c`.

---

## 1. Python simulation (run this first)

Requires only Python 3.8+ and the standard library (no packages to install). Works on Windows, macOS and Linux.

```bash
cd python_simulation
python main.py                      # menu-driven demo, 30 s lockout
python main.py --fast               # 5 s lockout and quicker animations
python main.py --demo               # automatic walkthrough of every feature, then exit
python main.py --demo --fast        # same, with a 5 s lockout
python main.py --plain              # no colours or box characters (very old terminals)
python -m unittest -v               # 32 tests (no waiting, fake clock)
```

On Windows you can also double-click `run_demo.bat` in the project root (needs Python on PATH).

In VS Code: open the `password-security-lpc1768` folder, open a terminal (Ctrl+`), `cd python_simulation`, run a command above. **Maximise the terminal panel** (the up-arrow button in its toolbar) so the whole screen is visible. On Windows use `python` or `py`.

### Using the demo

Menu: `1` enter password, `2` authentication history, `3` system information, `4` automatic demo, `0` exit.

At the password prompt type the 4 digits and press Enter. **What you type is hidden**; the virtual LCD shows `****`. `*` clears the entry, and pressing Enter on its own returns to the menu. An unfinished entry (fewer than 4 digits) is discarded and not counted as an attempt.

Options: `--password 4821`, `--attempts 3`, `--lockout 30`.

Everything on screen (LCD, green/red LED, buzzer) is **drawn as text; nothing is connected to real hardware**, and the interface says so.

### Files

- `auth_core.py` - the logic (password check, attempt count, lockout). No printing or sleeping; clock is injectable for tests.
- `virtual_board.py` - the simulated LCD, LEDs and buzzer. Its `signal_*()` methods are the single place that decides LED and buzzer states.
- `history.py` - session log of attempts (the digits typed are never stored).
- `screens.py` - builds each screen (menu, entry, granted/denied, lockout, history, info).
- `ui.py` - colours, boxes and screen-drawing helpers.
- `main.py` - program flow: start-up, menu, authentication, lockout, demo.
- `config.py` - password, attempts, lockout time, team names.
- `test_auth.py`, `test_board.py`, `test_interface.py` - tests.

---

## 2. LPC1768 firmware

Modules (all pin numbers are in `config.h`):

| File | Job |
|---|---|
| `main.c` | Main loop and screens |
| `auth.c/.h` | Password, attempts, lockout bookkeeping (pure C, no hardware) |
| `keypad.c/.h` | 4x4 matrix scan with debounce |
| `lcd.c/.h` | 16x2 LCD, 4-bit mode |
| `indicators.c/.h` | LEDs and buzzer |
| `timer.c/.h` | Timer0 1 ms tick (drives the 30 s lockout) and delays |
| `config.h` | Settings and pin mapping |

### Pin mapping (from the synopsis)

| Signal | Pin |
|---|---|
| Keypad rows 1-4 | P2.10, P2.11, P2.12, P2.13 |
| Keypad columns 1-4 | P1.23, P1.24, P1.25, P1.26 |
| LCD D4, D5, D6, D7 | P0.23, P0.24, P0.25, P0.26 |
| LCD RS / EN | P0.27 / P0.28 |
| Green LED (Purpose LED 1) | P0.4 |
| Red LED (Purpose LED 2) | P0.5 |
| Buzzer | **not given in the synopsis** - see below |

Board connections: keypad CNB to CNB3 (10-pin FRC, short JP4 1-2); LCD CND to CNAD (short JP16 and JP5, adjust POT3 for contrast).

### Things to check before running on the board

1. **Buzzer pin.** The synopsis says only "on-board buzzer". `BUZZER_PIN` in `config.h` is a placeholder (P0.8). Look it up in the ALS manual and set it, plus `BUZZER_ACTIVE_HIGH` if the buzzer is active-low.
2. **Keypad direction.** The code drives columns low and reads rows. If keys read wrong or not at all, check the board's wiring/manual and swap the roles.
3. **Key layout.** `keymap` in `keypad.c` assumes `123A / 456B / 789C / *0#D`.

### Build in Keil uVision

1. New project, device **NXP LPC1768** (accept the startup file; this brings in `LPC17xx.h`, `system_LPC17xx.c`).
2. Add the `.c` files from `firmware/` to the project and add `firmware/` to the include path.
3. Build, flash through your USB/serial connection, reset.

### Verification status

Checked here: the 32 Python tests pass; the interface was run in a real pseudo-terminal (hidden password entry, colours, a real 30 s lockout measured at 30.1 s); `auth.c` compiles and passes a native test of the lockout logic; all firmware files pass a syntax check against a stub header. **Not tested on Windows, and not tested on real hardware** - pin wiring and timing still need a check on the board.
