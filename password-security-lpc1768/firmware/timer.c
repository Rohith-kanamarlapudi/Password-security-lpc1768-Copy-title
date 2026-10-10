#include "timer.h"
#include "LPC17xx.h"

static volatile uint32_t ms_ticks;

void timer_init(void)
{
    uint32_t pclk;

    ms_ticks = 0;

    LPC_SC->PCONP   |= (1u << 1);          /* power Timer0 */
    LPC_SC->PCLKSEL0 &= ~(3u << 2);        /* Timer0 PCLK = CCLK/4 (reset default) */
    pclk = SystemCoreClock / 4u;

    LPC_TIM0->TCR = 0x02;                  /* reset counter */
    LPC_TIM0->PR  = (pclk / 1000000u) - 1u;/* TC counts in 1 us steps */
    LPC_TIM0->MR0 = 999u;                  /* match every 1000 us = 1 ms */
    LPC_TIM0->MCR = 0x03;                  /* interrupt + reset on MR0 */
    LPC_TIM0->IR  = 0x01;                  /* clear any pending flag */

    NVIC_EnableIRQ(TIMER0_IRQn);
    LPC_TIM0->TCR = 0x01;                  /* start */
}

void TIMER0_IRQHandler(void)
{
    if (LPC_TIM0->IR & 0x01) {
        LPC_TIM0->IR = 0x01;               /* clear MR0 interrupt */
        ms_ticks++;
    }
}

uint32_t millis(void)
{
    return ms_ticks;
}

void delay_ms(uint32_t ms)
{
    uint32_t start = ms_ticks;
    while ((uint32_t)(ms_ticks - start) < ms) {
        /* wait */
    }
}

void delay_us(uint32_t us)
{
    /* rough busy-wait; ~4 cycles per loop iteration */
    volatile uint32_t n = us * (SystemCoreClock / 4000000u) + 1u;
    while (n--) {
        __NOP();
    }
}
