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

//! \file
//! \brief How to wait for the right moment to send a spike.

#ifndef _SPIKE_SEND_DELAY_H_
#define _SPIKE_SEND_DELAY_H_

#include <sark.h>
#include <stdbool.h>

//! \brief Computes the initial value for the `expected_time` argument to
//!     need_to_wait_for_send_time()
//! \param[in] timer_period: The phase unit
//! \return The initial expected time
static inline uint expected_spike_wait_time(uint timer_period) {
    return sv->cpu_clk * timer_period;
}

//! \brief Determines whether a wait is needed
//! \param[in] timer_count: The current time in simulation ticks
//! \param[in] expected_time: The point when we expect to send
//! \return Whether we need to wait before sending the next packet.
static inline bool need_to_wait_for_send_time(
        uint timer_count, uint expected_time) {
    // Spin1 API ticks - to know when the timer wraps
    // TODO: Does this need to be volatile?
    extern uint ticks;

    return (ticks == timer_count) && (tc[T1_COUNT] > expected_time);
}

#endif // _SPIKE_SEND_DELAY_H_
