#include "auth.h"
#include "config.h"
#include <string.h>

static char     entry[PASSWORD_LENGTH + 1];
static uint8_t  entry_len;
static uint8_t  failed;
static uint32_t lockout_end_ms;

void auth_init(void)
{
    entry_len = 0;
    entry[0] = '\0';
    failed = 0;
    lockout_end_ms = 0;
}

/* Compares every character so timing does not reveal where a mismatch is. */
static int password_matches(const char *candidate)
{
    const char *secret = DEFAULT_PASSWORD;
    uint8_t diff = 0;
    uint8_t i;
    for (i = 0; i < PASSWORD_LENGTH; i++) {
        diff |= (uint8_t)(candidate[i] ^ secret[i]);
    }
    return diff == 0;
}

auth_event_t auth_key(char key)
{
    if (key == CLEAR_KEY) {
        entry_len = 0;
        entry[0] = '\0';
        return AUTH_EV_CLEARED;
    }
    if (key < '0' || key > '9') {
        return AUTH_EV_NONE;               /* A-D and '#' unused */
    }

    entry[entry_len++] = key;
    entry[entry_len] = '\0';
    if (entry_len < PASSWORD_LENGTH) {
        return AUTH_EV_DIGIT;
    }

    /* full password entered */
    {
        int ok = password_matches(entry);
        entry_len = 0;
        entry[0] = '\0';
        if (ok) {
            failed = 0;
            return AUTH_EV_GRANTED;
        }
        failed++;
        return AUTH_EV_DENIED;
    }
}

uint8_t auth_entry_length(void)    { return entry_len; }
uint8_t auth_failed_attempts(void) { return failed; }
int     auth_lockout_pending(void) { return failed >= MAX_ATTEMPTS; }

void auth_lockout_start(uint32_t now_ms)
{
    lockout_end_ms = now_ms + (uint32_t)LOCKOUT_SECONDS * 1000u;
}

uint32_t auth_lockout_remaining_ms(uint32_t now_ms)
{
    /* signed difference keeps this correct even if the tick wraps */
    int32_t left = (int32_t)(lockout_end_ms - now_ms);
    return (left > 0) ? (uint32_t)left : 0u;
}

void auth_lockout_end(void)
{
    failed = 0;
    entry_len = 0;
    entry[0] = '\0';
}
