"""Console stand-in for the trainer board's LCD, LEDs and buzzer.

Nothing here talks to real hardware. It remembers what the LCD, LEDs and
buzzer *would* be doing and draws them as text.

The signal_*() methods are the ONE place that decides which LED / buzzer
state goes with each system state, so the rule "buzzer sounds only after a
failed attempt" lives in exactly one spot.
"""

import ui

LCD_WIDTH = 16


class VirtualBoard:
    def __init__(self):
        self.line1 = ""
        self.line2 = ""
        self.green_led = False   # on-board Purpose LED 1
        self.red_led = False     # on-board Purpose LED 2
        self.buzzer = False

    # ---- raw outputs --------------------------------------------------------
    def lcd(self, line1="", line2=""):
        self.line1 = line1[:LCD_WIDTH]
        self.line2 = line2[:LCD_WIDTH]

    def leds(self, green=False, red=False):
        self.green_led, self.red_led = green, red

    # ---- LED + buzzer pattern for each system state ---------------------------
    def signal_idle(self):
        self.leds()
        self.buzzer = False

    def signal_granted(self):
        self.leds(green=True)
        self.buzzer = False          # a correct password never sounds the buzzer

    def signal_denied(self):
        self.leds(red=True)
        self.buzzer = True           # the only state in which the buzzer is on

    def signal_locked(self):
        self.leds(red=True)
        self.buzzer = False

    # ---- drawing -----------------------------------------------------------
    def lcd_lines(self):
        """The 16x2 LCD: dark characters on a yellow-green background, in a bezel."""
        def row(text):
            cells = " ".join(text.ljust(LCD_WIDTH))          # 31 characters wide
            return (ui.paint(ui.g("v"), "bezel")
                    + ui.paint(f" {cells} ", "lcd")
                    + ui.paint(ui.g("v"), "bezel"))

        span = ui.g("h") * 33
        top = ui.paint(ui.g("stl") + span + ui.g("str"), "bezel")
        bottom = ui.paint(ui.g("sbl") + span + ui.g("sbr"), "bezel")
        return [top, row(self.line1), row(self.line2), bottom]

    def indicator_line(self):
        def cell(label, is_on, color, on_word, on_symbol, off_symbol):
            if is_on:
                state = ui.paint(f"{on_symbol} {on_word}", "bold", color)
            else:
                state = ui.paint(f"{off_symbol} off", "gray")
            return ui.pad(f"{label}  {state}", 20)

        return (
            cell("GREEN LED", self.green_led, "green", "ON", ui.g("led_on"), ui.g("led_off"))
            + cell("RED LED", self.red_led, "red", "ON", ui.g("led_on"), ui.g("led_off"))
            + cell("BUZZER", self.buzzer, "yellow", "SOUNDING", ui.g("buz_on"), ui.g("buz_off"))
        )

    def panel(self):
        """The whole simulated-output panel as a list of lines."""
        inner = ui.WIDTH - 4
        body = [ui.center(line, inner) for line in self.lcd_lines()]
        body.append("")
        body.append(ui.center(self.indicator_line(), inner))
        return ui.box(body, title="SIMULATED BOARD OUTPUT (no hardware connected)", color="blue")
