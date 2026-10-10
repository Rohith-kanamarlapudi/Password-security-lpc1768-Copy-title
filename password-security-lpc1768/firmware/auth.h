/*
 * auth.h - password check, attempt counter and lockout bookkeeping.
 * Pure C: no hardware access, so it can also be compiled and tested on a PC.
 * (C twin of python_simulation/auth_core.py)
 */
#ifndef AUTH_H
#define AUTH_H

#include <stdint.h>

typedef enum {
    AUTH_EV_NONE = 0,   /* key ignored */
    AUTH_EV_DIGIT,      /* digit accepted, still collecting */
    AUTH_EV_CLEARED,    /* entry cleared */
    AUTH_EV_GRANTED,    /* correct password */
    AUTH_EV_DENIED      /* wrong password */
} auth_event_t;

void         auth_init(void);
auth_event_t auth_key(char key);           /* feed one keypad key */
uint8_t      auth_entry_length(void);      /* digits entered so far */
uint8_t      auth_failed_attempts(void);
int          auth_lockout_pending(void);   /* 1 when max attempts reached */

/* Lockout timing uses a millisecond tick supplied by the caller. */
void         auth_lockout_start(uint32_t now_ms);
uint32_t     auth_lockout_remaining_ms(uint32_t now_ms);  /* 0 = finished */
void         auth_lockout_end(void);       /* resets the failed-attempt count */

#endif /* AUTH_H */
