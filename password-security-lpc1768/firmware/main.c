/*
 * main.c - Password-Based Security System, NXP LPC1768
 *          (ALS-SDA-ARMCTXM3-01 trainer board)
 *
 * Flow: init -> "Enter Password" -> read 4 digits -> granted / denied
 *       -> after 3 consecutive failures lock for 30 s -> resume.
 */
#include <stdio.h>
#include "LPC17xx.h"
#include "config.h"
#include "timer.h"
#include "lcd.h"
#include "keypad.h"
#include "indicators.h"
#include "auth.h"

static void show_entry_screen(void)
{
    char stars[LCD_COLUMNS + 1];
    uint8_t i, n = auth_entry_length();

    for (i = 0; i < n && i < LCD_COLUMNS; i++) stars[i] = '*';
    stars[i] = '\0';

    lcd_print_line(0, "Enter Password");
    lcd_print_line(1, stars);
}

static void do_access_granted(void)
{
    led_green(1);
    lcd_print_line(0, "Access Granted");
    lcd_print_line(1, "Welcome!");
    buzzer_beep(150);                    /* single beep */
    delay_ms(RESULT_DISPLAY_MS);
    led_green(0);
}

static void do_access_denied(void)
{
    char line[LCD_COLUMNS + 1];
    sprintf(line, "Attempt %u/%u", (unsigned)auth_failed_attempts(), (unsigned)MAX_ATTEMPTS);

    led_red(1);
    lcd_print_line(0, "Access Denied");
    lcd_print_line(1, line);
    buzzer(1);
    delay_ms(RESULT_DISPLAY_MS);
    buzzer(0);
    led_red(0);
}

static void do_lockout(void)
{
    char line[LCD_COLUMNS + 1];
    uint32_t remaining_ms;
    uint32_t last_secs = 0xFFFFFFFFu;

    auth_lockout_start(millis());
    led_red(1);
    lcd_print_line(0, "System Locked");

    /* keypad is not scanned in here, so presses are ignored */
    while ((remaining_ms = auth_lockout_remaining_ms(millis())) > 0) {
        uint32_t secs = (remaining_ms + 999u) / 1000u;   /* round up */
        if (secs != last_secs) {
            sprintf(line, "Wait %2lu sec", (unsigned long)secs);
            lcd_print_line(1, line);
            last_secs = secs;
        }
    }

    auth_lockout_end();
    led_red(0);
    lcd_print_line(0, "Lockout over");
    lcd_print_line(1, "Try again");
    delay_ms(1000);
}

int main(void)
{
    SystemInit();                        /* clocks (CMSIS startup normally does this) */

    timer_init();
    indicators_init();
    lcd_init();
    keypad_init();
    auth_init();

    lcd_print_line(0, "ALS LPC1768");
    lcd_print_line(1, "SECURITY SYSTEM");
    delay_ms(1500);

    show_entry_screen();

    for (;;) {
        char key = keypad_get_key();
        if (key == 0) {
            continue;
        }

        switch (auth_key(key)) {
        case AUTH_EV_DIGIT:
        case AUTH_EV_CLEARED:
            show_entry_screen();
            break;

        case AUTH_EV_GRANTED:
            do_access_granted();
            show_entry_screen();
            break;

        case AUTH_EV_DENIED:
            do_access_denied();
            if (auth_lockout_pending()) {
                do_lockout();
            }
            show_entry_screen();
            break;

        default:
            break;
        }
    }
}
