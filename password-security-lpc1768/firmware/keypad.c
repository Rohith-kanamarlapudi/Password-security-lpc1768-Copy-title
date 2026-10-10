#include "keypad.h"
#include "config.h"
#include "timer.h"
#include "LPC17xx.h"

#define ROW_MASK  (0xFu << KEYPAD_ROW_FIRST_PIN)   /* P2.10-P2.13 */
#define COL_MASK  (0xFu << KEYPAD_COL_FIRST_PIN)   /* P1.23-P1.26 */

/* Key layout - same as python_simulation/config.py. Verify against the board. */
static const char keymap[4][4] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'}
};

void keypad_init(void)
{
    LPC_PINCON->PINSEL4 &= ~(0xFFu << 20);          /* P2.10-P2.13 -> GPIO */
    LPC_PINCON->PINSEL3 &= ~(0xFFu << 14);          /* P1.23-P1.26 -> GPIO */

    LPC_GPIO2->FIODIR &= ~ROW_MASK;                 /* rows = inputs (pull-up by default) */
    LPC_GPIO1->FIODIR |=  COL_MASK;                 /* columns = outputs */
    LPC_GPIO1->FIOSET  =  COL_MASK;                 /* all columns idle high */
}

/* One raw scan: drive each column low in turn and look for a low row. */
static char scan_once(void)
{
    unsigned char col, row;
    uint32_t rows;

    for (col = 0; col < 4; col++) {
        LPC_GPIO1->FIOSET = COL_MASK;
        LPC_GPIO1->FIOCLR = 1u << (KEYPAD_COL_FIRST_PIN + col);
        delay_us(50);                               /* let the lines settle */

        rows = (LPC_GPIO2->FIOPIN >> KEYPAD_ROW_FIRST_PIN) & 0xFu;
        if (rows != 0xFu) {
            for (row = 0; row < 4; row++) {
                if (!(rows & (1u << row))) {
                    LPC_GPIO1->FIOSET = COL_MASK;
                    return keymap[row][col];
                }
            }
        }
    }
    LPC_GPIO1->FIOSET = COL_MASK;
    return 0;
}

char keypad_get_key(void)
{
    char key = scan_once();
    if (key == 0) {
        return 0;
    }

    delay_ms(20);                                   /* debounce */
    if (scan_once() != key) {
        return 0;
    }

    while (scan_once() != 0) {                      /* wait for release */
    }
    delay_ms(20);
    return key;
}
