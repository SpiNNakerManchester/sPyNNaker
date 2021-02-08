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
//! \brief Support code for last_neuron_selection_impl.h
#include "last_neuron_selection_impl.h"

spike_t* last_spikes_buffer[2];
uint32_t n_spikes[2];
//! Size of each sub-array within ::last_spikes_buffer
uint32_t last_spikes_buffer_size;
//! The time of the most recently-considered spike
uint32_t last_time;

void partner_init(uint8_t **data) {
    last_spikes_buffer_size = ((uint32_t *) *data)[0];
    log_debug("Last neuron selection, buffer size = %u", last_spikes_buffer_size);
    for (uint32_t i = 0; i < 2; i++) {
        last_spikes_buffer[i] =
                spin1_malloc(last_spikes_buffer_size * sizeof(spike_t));
        if (last_spikes_buffer[i] == NULL) {
            log_error("Out of memory when creating last spikes buffer");
            rt_error(RTE_SWERR);
        }
        n_spikes[i] = 0;
    }
    *data += sizeof(uint32_t);
}
