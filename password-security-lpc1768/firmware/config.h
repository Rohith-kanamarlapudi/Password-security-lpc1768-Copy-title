/*
 * config.h - all settings and pin mappings in one place.
 * Pin numbers come from the project synopsis (ALS-SDA-ARMCTXM3-01 board).
 */
#ifndef CONFIG_H
#define CONFIG_H

/* ---------------- Authentication settings ---------------- */
#define DEFAULT_PASSWORD     "1234"
#define PASSWORD_LENGTH      4
#define MAX_ATTEMPTS         3
#define LOCKOUT_SECONDS      30
#define RESULT_DISPLAY_MS    2000u   /* "Access Granted/Denied" display time */
#define CLEAR_KEY            '*'

/* ---------------- 4x4 keypad (CNB - CNB3) ----------------
 * Rows    : P2.10 - P2.13  (inputs, internal pull-ups)
 * Columns : P1.23 - P1.26  (outputs, driven low one at a time)
 */
#define KEYPAD_ROW_FIRST_PIN  10     /* P2.10 = Row 1 ... P2.13 = Row 4 */
#define KEYPAD_COL_FIRST_PIN  23     /* P1.23 = Col 1 ... P1.26 = Col 4 */

/* ---------------- 16x2 LCD, 4-bit mode (CND - CNAD) ----------------
 * D4-D7 : P0.23 - P0.26     RS : P0.27     EN : P0.28
 * (RW is tied low on the board.)
 */
#define LCD_DATA_FIRST_PIN    23     /* D4=P0.23, D5=P0.24, D6=P0.25, D7=P0.26 */
#define LCD_RS_PIN            27
#define LCD_EN_PIN            28
#define LCD_COLUMNS           16

/* ---------------- LEDs and buzzer ----------------
 * Purpose LED 1 (green) = P0.4, Purpose LED 2 (red) = P0.5.
 *
 * !! The synopsis only says "on-board buzzer" and gives NO port pin. !!
 * BUZZER_PIN below is a PLACEHOLDER (P0.8). Check the ALS-SDA-ARMCTXM3-01
 * manual / schematic and change it (and BUZZER_ACTIVE_HIGH if needed).
 */
#define LED_GREEN_PIN         4      /* P0.4 */
#define LED_RED_PIN           5      /* P0.5 */
#define BUZZER_PIN            8      /* P0.8  <-- VERIFY IN BOARD MANUAL */
#define BUZZER_ACTIVE_HIGH    1

#endif /* CONFIG_H */
