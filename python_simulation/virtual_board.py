"""Console stand-in for the trainer board's LCD, LEDs and buzzer.

Uses plain ASCII only so it renders correctly in any VS Code terminal.
"""

LCD_WIDTH = 16


class VirtualBoard:
    def __init__(self):
        self.line1 = ""
        self.line2 = ""
        self.green_led = False   # on-board Purpose LED 1
        self.red_led = False     # on-board Purpose LED 2
        self.buzzer = False

    def lcd(self, line1="", line2=""):
        self.line1 = line1[:LCD_WIDTH]
        self.line2 = line2[:LCD_WIDTH]

    def leds(self, green=False, red=False):
        self.green_led, self.red_led = green, red

    def render(self):
        def on(v, name):
            return f"{name}:[{'ON ' if v else 'off'}]"

        print("  +" + "-" * LCD_WIDTH + "+")
        print(f"  |{self.line1:<{LCD_WIDTH}}|")
        print(f"  |{self.line2:<{LCD_WIDTH}}|")
        print("  +" + "-" * LCD_WIDTH + "+")
        print(
            "  "
            + on(self.green_led, "GREEN LED")
            + "  "
            + on(self.red_led, "RED LED")
            + "  "
            + on(self.buzzer, "BUZZER")
        )
        print()
