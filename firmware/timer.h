/*
 * timer.h - 1 ms system tick on Timer0, plus delay helpers.
 * The lockout period is measured with this tick.
 */
#ifndef TIMER_H
#define TIMER_H

#include <stdint.h>

void     timer_init(void);          /* start Timer0, 1 ms interrupt */
uint32_t millis(void);              /* ms since timer_init() */
void     delay_ms(uint32_t ms);     /* needs timer_init() first */
void     delay_us(uint32_t us);     /* short busy-wait (LCD / keypad) */

#endif /* TIMER_H */
