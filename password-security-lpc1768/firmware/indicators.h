/* indicators.h - on-board LEDs and buzzer. */
#ifndef INDICATORS_H
#define INDICATORS_H

#include <stdint.h>

void indicators_init(void);
void led_green(int on);
void led_red(int on);
void buzzer(int on);
void buzzer_beep(uint32_t ms);   /* blocking beep */

#endif /* INDICATORS_H */
