/**
 *! \file
 *! \brief Common functions for matrix generation
 */

#ifndef __MATRIX_GENERATOR_COMMON_H__
#define __MATRIX_GENERATOR_COMMON_H__

#include <debug.h>

/**
 *! \brief The maximum delay value that can be represented on core
 */
#define MAX_DELAY 16

/**
 *! \brief A converted final delay value and delay stage
 */
struct delay_value {
    uint16_t delay;
    uint16_t stage;
};

/**
 *! \brief Get a converted delay value and stage
 *! \param[in] The value to convert
 *! \param[in] The maximum delay stage allowed
 */
struct delay_value get_delay(uint16_t delay_value, uint32_t max_stage) {
    uint16_t delay = delay_value;

    // Ensure delay is at least 1
    if (delay < 1) {
        log_debug("Delay of %u is too small", delay);
        delay = 1;
    }

    // Ensure that the delay is less than the maximum
    uint16_t stage = (delay - 1) / MAX_DELAY;
    if (stage >= max_stage) {
        log_debug("Delay of %u is too big", delay);
        stage = max_stage - 1;
        delay = (stage * MAX_DELAY);
    }

    // Get the remainder of the delay
    delay = ((delay - 1) % MAX_DELAY) + 1;
    return (struct delay_value) {.delay = delay, .stage = stage};
}

#endif // __MATRIX_GENERATOR_COMMON_H__
