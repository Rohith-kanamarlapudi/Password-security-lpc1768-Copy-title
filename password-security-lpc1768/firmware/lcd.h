/* lcd.h - 16x2 HD44780 LCD in 4-bit mode. */
#ifndef LCD_H
#define LCD_H

void lcd_init(void);
void lcd_clear(void);
void lcd_print_line(unsigned char row, const char *text);  /* row 0 or 1, padded to 16 chars */

#endif /* LCD_H */
