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

#include <stdint.h>
#include <stdbool.h>
#include <spin1_api.h>
#include <spin1_api_params.h>
#include "plasticity/synapse_dynamics.h"

//! Key from neruon.c
extern uint32_t key;

//! Whether to use key from neuron.c
extern bool use_key;

//! Earliest time from neuron.c
extern uint32_t earliest_send_time;

//! Latest time from neuron.c
extern uint32_t latest_send_time;

//! Mask to recognise the Comms Controller "not full" flag
#define TX_NOT_FULL_MASK 0x10000000

//! \brief Perform direct spike sending with hardware for speed
//! \param[in] key The key to send
static inline void send_spike_mc(uint32_t key) {
    // Wait for there to be space to send
    uint32_t n_loops = 0;
    while (!(cc[CC_TCR] & TX_NOT_FULL_MASK) && (n_loops < 10000)) {
        spin1_delay_us(1);
        n_loops++;
    }
    if (!(cc[CC_TCR] & TX_NOT_FULL_MASK)) {
        io_printf(IO_BUF, "[ERROR] Couldn't send spike; TCR=0x%08x\n", cc[CC_TCR]);
        rt_error(RTE_SWERR);
    }

    // Do the send
    cc[CC_TCR] = PKT_MC;
    cc[CC_TXKEY]  = key;
}

//! \brief Performs the sending of a spike.  Inlined for speed.
//! \param[in] timer_count The global timer count when the time step started
//! \param[in] time The current time step
//! \param[in] The neuron index to send
static inline void send_spike(UNUSED uint32_t timer_count, uint32_t time,
        uint32_t neuron_index) {
    // Do any required synapse processing
//    synapse_dynamics_process_post_synaptic_event(time, neuron_index);

    if (use_key) {
        send_spike_mc(key | neuron_index);

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
