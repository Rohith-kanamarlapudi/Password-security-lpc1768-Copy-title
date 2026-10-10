/* keypad.h - 4x4 matrix keypad scanner. */
#ifndef KEYPAD_H
#define KEYPAD_H

void keypad_init(void);
char keypad_get_key(void);   /* returns one debounced key press, or 0 if none (non-blocking) */

#endif /* KEYPAD_H */
