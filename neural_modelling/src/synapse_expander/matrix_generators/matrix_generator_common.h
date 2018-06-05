#ifndef __MATRIX_GENERATOR_COMMON_H__
#define __MATRIX_GENERATOR_COMMON_H__

#include <debug.h>

#define MAX_DELAY 16

struct delay_value {
    uint16_t delay;
    uint16_t stage;
};

struct delay_value get_delay(uint16_t delay_value, uint32_t max_stage) {
    uint16_t delay = delay_value;
    if (delay < 1) {
        log_debug("Delay of %u is too small", delay);
        delay = 1;
    }
    uint16_t stage = (delay - 1) / MAX_DELAY;
    if (stage >= max_stage) {
        log_debug("Delay of %u is too big", delay);
        stage = max_stage - 1;
        delay = (stage * MAX_DELAY);
    }
    delay = ((delay - 1) % MAX_DELAY) + 1;
    return (struct delay_value) {.delay = delay, .stage = stage};
}

#endif // __MATRIX_GENERATOR_COMMON_H__
