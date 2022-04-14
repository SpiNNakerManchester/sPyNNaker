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
//! \brief Recently spiked partners selection rule
#ifndef _LAST_NEURON_SELECTION_IMPL_H_
#define _LAST_NEURON_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>

//! \brief Spike accumulation buffers
//! \details Two arrays, one for current timestep, one for previous
extern spike_t* last_spikes_buffer[2];
//! \brief Spike buffer counters
//! \details Two counters, one for current timestep, one for previous
extern uint32_t n_spikes[2];

//! \brief Notifies the rule that a spike has been received
//! \param[in] time: The time that the spike was received at
//! \param[in] spike:
//!     The spike that was received (includes the sending neuron ID)
static inline void partner_spike_received(uint32_t time, spike_t spike) {
    extern uint32_t last_spikes_buffer_size;
    extern uint32_t last_time;

    uint32_t buffer = time & 0x1;
    if (time != last_time) {
        last_time = time;
        n_spikes[buffer] = 0;
    }
    if (n_spikes[buffer] < last_spikes_buffer_size) {
        last_spikes_buffer[buffer][n_spikes[buffer]++] = spike;
    }
}

//! \brief Choose the potential (remote) synaptic partner
//! \details Randomly (with uniform probability) select one of the last received
//!     spikes, and uses the source neuron from that.
//! \param[in] time: The current time
//! \param[out] population_id: The ID of the other population
//! \param[out] sub_population_id: The ID of the subpopulation (corresponds to
//!     remote SpiNNaker core handling the population)
//! \param[out] neuron_id: The ID of the neuron within the subpopulation
//! \param[out] spike: The spike that made this a meaningful choice
//! \param[out] m_pop_index: The master population table index
//! \return True if a choice was made
static inline bool potential_presynaptic_partner(
        uint32_t time, uint32_t *restrict population_id,
        uint32_t *restrict sub_population_id, uint32_t *restrict neuron_id,
        spike_t *restrict spike, uint32_t *restrict m_pop_index) {
    extern rewiring_data_t rewiring_data;
    extern pre_pop_info_table_t pre_info;

    uint32_t buffer = (time - 1) & 0x1;
    if (!n_spikes[buffer]) {
        return false;
    }
    uint32_t offset = rand_int(n_spikes[buffer], rewiring_data.local_seed);
    *spike = last_spikes_buffer[buffer][offset];
    return sp_structs_find_by_spike(&pre_info, *spike, neuron_id,
            population_id, sub_population_id, m_pop_index);
}

#endif // _LAST_NEURON_SELECTION_IMPL_H_
