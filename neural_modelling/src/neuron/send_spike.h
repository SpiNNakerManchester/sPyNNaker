/*
 * Copyright (c) 2021 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

//! The time step colour to account for delay
extern uint32_t colour;

//! \brief Performs the sending of a spike.  Inlined for speed.
//! \param[in] timer_count The global timer count when the time step started
//! \param[in] time The current time step
//! \param[in] The neuron index to send
static inline void send_spike(UNUSED uint32_t timer_count, uint32_t time,
        uint32_t neuron_index) {
    // Do any required synapse processing
    synapse_dynamics_process_post_synaptic_event(time, neuron_index);

    if (use_key) {
        send_spike_mc(neuron_keys[neuron_index] | colour);

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
