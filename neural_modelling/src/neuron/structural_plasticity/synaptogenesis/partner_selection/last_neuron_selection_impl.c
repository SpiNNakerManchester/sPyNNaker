/*
 * Copyright (c) 2017 The University of Manchester
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
