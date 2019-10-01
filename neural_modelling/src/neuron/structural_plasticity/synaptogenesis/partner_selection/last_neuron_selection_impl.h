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

#ifndef _LAST_NEURON_SELECTION_IMPL_H_
#define _LAST_NEURON_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>

// Include debug header for log_info etc
#include <debug.h>

extern spike_t* last_spikes_buffer[2];
extern uint32_t n_spikes[2];
extern uint32_t last_spikes_buffer_size;
extern uint32_t last_time;
extern rewiring_data_t rewiring_data;
extern pre_pop_info_table_t pre_info;

static inline void partner_spike_received(uint32_t time, spike_t spike) {
    uint32_t buffer = time & 0x1;
    if (time != last_time) {
        last_time = time;
        n_spikes[buffer] = 0;
    }
    if (n_spikes[buffer] < last_spikes_buffer_size) {
        last_spikes_buffer[buffer][n_spikes[buffer]++] = spike;
    }
}

//! randomly (with uniform probability) select one of the last received spikes
static inline bool potential_presynaptic_partner(
        uint32_t time, uint32_t *population_id, uint32_t *sub_population_id,
        uint32_t *neuron_id, spike_t *spike, uint32_t *m_pop_index) {
    uint32_t buffer = (time - 1) & 0x1;
    if (!n_spikes[buffer]) {
        return false;
    }
    uint32_t offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        n_spikes[buffer];
    *spike = last_spikes_buffer[buffer][offset];
    return sp_structs_find_by_spike(&pre_info, *spike, neuron_id,
            population_id, sub_population_id, m_pop_index);
}

#endif // _LAST_NEURON_SELECTION_IMPL_H_
