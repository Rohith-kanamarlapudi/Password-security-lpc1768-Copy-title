# Password-Based Security System Using NXP LPC1768

Mini project for the ALS-SDA-ARMCTXM3-01 trainer board (4x4 keypad, 16x2 LCD, LEDs, buzzer).

The project has two independent parts:

| Folder | What it is | Needs hardware? |
|---|---|---|
| `python_simulation/` | Laptop demo of the full behaviour | No |
| `firmware/` | Embedded C for the LPC1768 (Keil uVision) | Yes |

## Behaviour (same in both)

- Enter a 4-digit password on the keypad. Default password: `1234`.
- Correct: LCD shows **Access Granted**, green LED on, one beep, attempt counter resets.
- Wrong: LCD shows **Access Denied** and the attempt number, red LED on, buzzer on.
- After **3 consecutive** wrong attempts: **System Locked** for **30 seconds** with a live countdown. Keys are ignored during lockout.
- After the lockout the system returns to "Enter Password".
- `*` clears the digits typed so far. `A-D` and `#` are unused.

---

## 1. Python simulation (run this first)

Requires only Python 3.8+ (no packages to install).

```bash
cd python_simulation
python main.py              # interactive, 30 s lockout
python main.py --fast       # 5 s lockout, short pauses
python main.py --demo --lockout 3   # scripted walkthrough of every feature
python -m unittest -v       # 12 unit tests (no waiting, fake clock)
```

In VS Code: open the `password-security-lpc1768` folder, open a terminal, `cd python_simulation`, run the commands above.

At the `Keypad>` prompt type digits and press Enter, e.g. `1234` or `1111`. You can type one key or all four at once. Type `q` to quit.

Options: `--password 4821`, `--attempts 3`, `--lockout 30`.

Files:

- `auth_core.py` - the logic (password check, attempt count, lockout). No printing or sleeping; clock is injectable for tests.
- `virtual_board.py` - draws the LCD, LEDs and buzzer in the terminal.
- `main.py` - interactive CLI and scripted demo.
- `config.py` - password, attempts, lockout time.
- `test_auth.py` - unit tests.

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

Checked here: the Python tests and demo run, `auth.c` compiles and passes a native test of the lockout logic, and all firmware files pass a syntax check against a stub header. **Not tested on real hardware** - pin wiring and timing still need a check on the board.
