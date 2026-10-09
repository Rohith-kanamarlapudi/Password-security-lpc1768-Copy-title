#include "lcd.h"
#include "config.h"
#include "timer.h"
#include "LPC17xx.h"

#define LCD_DATA_MASK  (0xFu << LCD_DATA_FIRST_PIN)   /* P0.23-P0.26 */
#define LCD_RS_MASK    (1u << LCD_RS_PIN)             /* P0.27 */
#define LCD_EN_MASK    (1u << LCD_EN_PIN)             /* P0.28 */
#define LCD_ALL_MASK   (LCD_DATA_MASK | LCD_RS_MASK | LCD_EN_MASK)

static void lcd_pulse_enable(void)
{
    LPC_GPIO0->FIOSET = LCD_EN_MASK;
    delay_us(2);
    LPC_GPIO0->FIOCLR = LCD_EN_MASK;
    delay_us(50);                       /* most commands need < 40 us */
}

static void lcd_write_nibble(unsigned char nibble)
{
    LPC_GPIO0->FIOCLR = LCD_DATA_MASK;
    LPC_GPIO0->FIOSET = ((uint32_t)(nibble & 0x0Fu)) << LCD_DATA_FIRST_PIN;
    lcd_pulse_enable();
}

static void lcd_write_byte(unsigned char value, int is_data)
{
    if (is_data) LPC_GPIO0->FIOSET = LCD_RS_MASK;
    else         LPC_GPIO0->FIOCLR = LCD_RS_MASK;

    lcd_write_nibble(value >> 4);       /* high nibble first */
    lcd_write_nibble(value & 0x0F);
}

void lcd_init(void)
{
    /* P0.23-P0.28 as plain GPIO outputs */
    LPC_PINCON->PINSEL1 &= ~(0xFFFu << 14);         /* P0.23-P0.28 -> GPIO */
    LPC_GPIO0->FIODIR   |= LCD_ALL_MASK;
    LPC_GPIO0->FIOCLR    = LCD_ALL_MASK;

    delay_ms(20);                                   /* power-up wait */

    /* reset sequence to force 4-bit mode */
    LPC_GPIO0->FIOCLR = LCD_RS_MASK;
    lcd_write_nibble(0x3); delay_ms(5);
    lcd_write_nibble(0x3); delay_ms(1);
    lcd_write_nibble(0x3); delay_ms(1);
    lcd_write_nibble(0x2); delay_ms(1);

    lcd_write_byte(0x28, 0);   /* 4-bit, 2 lines, 5x8 font */
    lcd_write_byte(0x0C, 0);   /* display on, cursor off */
    lcd_write_byte(0x06, 0);   /* auto-increment cursor */
    lcd_clear();
}

void lcd_clear(void)
{
    lcd_write_byte(0x01, 0);
    delay_ms(2);               /* clear needs ~1.6 ms */
}

void lcd_print_line(unsigned char row, const char *text)
{
    unsigned char col = 0;
    lcd_write_byte((unsigned char)(0x80 | (row ? 0x40 : 0x00)), 0);  /* set cursor */

    while (*text && col < LCD_COLUMNS) {
        lcd_write_byte((unsigned char)*text++, 1);
        col++;
    }
    while (col < LCD_COLUMNS) {                     /* pad to erase old text */
        lcd_write_byte(' ', 1);
        col++;
    }
}
