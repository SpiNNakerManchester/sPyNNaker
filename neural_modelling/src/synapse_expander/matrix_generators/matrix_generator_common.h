/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * \dir
 * \brief Synaptic matrix generators
 * \file
 * \brief Common functions for matrix generation
 */

#ifndef __MATRIX_GENERATOR_COMMON_H__
#define __MATRIX_GENERATOR_COMMON_H__

#include <debug.h>

/**
 * \brief A converted final delay value and delay stage
 */
struct delay_value {
    uint16_t delay;
    uint16_t stage;
};

/**
 * \brief Get a converted delay value and stage
 * \param[in] delay_value: The value to convert
 * \param[in] max_stage: The maximum delay stage allowed
 * \param[in] max_delay_per_stage: The max delay in a delay stage
 * \return The converted delay value
 */
static struct delay_value get_delay(
        uint16_t delay_value, uint32_t max_stage,
        uint32_t max_delay_per_stage) {
    uint16_t delay = delay_value;

    // Ensure delay is at least 1
    if (delay < 1) {
        log_debug("Delay of %u is too small", delay);
        delay = 1;
    }

    // Ensure that the delay is less than the maximum
    uint16_t stage = (delay - 1) / max_delay_per_stage;
    if (stage >= max_stage) {
        log_debug("Delay of %u is too big", delay);
        stage = max_stage - 1;
        delay = (stage * max_delay_per_stage);
    }

    // Get the remainder of the delay
    delay = ((delay - 1) % max_delay_per_stage) + 1;
    return (struct delay_value) {.delay = delay, .stage = stage};
}

#endif // __MATRIX_GENERATOR_COMMON_H__
