#include "indicators.h"
#include "config.h"
#include "timer.h"
#include "LPC17xx.h"

#define GREEN_MASK   (1u << LED_GREEN_PIN)     /* P0.4 */
#define RED_MASK     (1u << LED_RED_PIN)       /* P0.5 */
#define BUZZER_MASK  (1u << BUZZER_PIN)        /* see config.h - verify pin */

static void set_pin(uint32_t mask, int on)
{
    if (on) LPC_GPIO0->FIOSET = mask;
    else    LPC_GPIO0->FIOCLR = mask;
}

void indicators_init(void)
{
    LPC_PINCON->PINSEL0 &= ~((3u << (LED_GREEN_PIN * 2)) |
                             (3u << (LED_RED_PIN * 2)) |
                             (3u << (BUZZER_PIN * 2)));   /* GPIO function */
    LPC_GPIO0->FIODIR |= GREEN_MASK | RED_MASK | BUZZER_MASK;

    led_green(0);
    led_red(0);
    buzzer(0);
}

void led_green(int on) { set_pin(GREEN_MASK, on); }
void led_red(int on)   { set_pin(RED_MASK, on); }

void buzzer(int on)
{
    set_pin(BUZZER_MASK, BUZZER_ACTIVE_HIGH ? on : !on);
}

void buzzer_beep(uint32_t ms)
{
    buzzer(1);
    delay_ms(ms);
    buzzer(0);
}
