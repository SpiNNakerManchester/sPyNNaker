/*
 * Copyright (c) 2021 The University of Manchester
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
#ifndef __SEND_SPIKE_H__
#define __SEND_SPIKE_H__

#include "plasticity/synapse_dynamics.h"
#include <common/send_mc.h>

//! Whether to use key from neuron.c
extern bool use_key;

//! Keys for each neuron
extern uint32_t *neuron_keys;

//! Earliest time from neuron.c
extern uint32_t earliest_send_time;

//! Latest time from neuron.c
extern uint32_t latest_send_time;

//! \brief Performs the sending of a spike.  Inlined for speed.
//! \param[in] timer_count The global timer count when the time step started
//! \param[in] time The current time step
//! \param[in] The neuron index to send
static inline void send_spike(UNUSED uint32_t timer_count, uint32_t time,
        uint32_t neuron_index) {
    // Do any required synapse processing
    synapse_dynamics_process_post_synaptic_event(time, neuron_index);

    if (use_key) {
        send_spike_mc(neuron_keys[neuron_index]);

        // Keep track of provenance data
        uint32_t clocks = tc[T1_COUNT];
        if (clocks > earliest_send_time) {
            earliest_send_time = clocks;
        }
        if (clocks < latest_send_time) {
            latest_send_time = clocks;
        }
    }
}

#endif // __SEND_SPIKE_H__
