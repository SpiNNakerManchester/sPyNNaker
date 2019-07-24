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
 *! \file
 *! \brief All-to-All connection generator implementation
 */

#include <stdbool.h>

/**
 *! \brief The parameters to be passed around for this connector
 */
struct all_to_all {
    uint32_t allow_self_connections;
};

void *connection_generator_all_to_all_initialise(address_t *region) {

    // Allocate the data structure for parameters
    struct all_to_all *params = (struct all_to_all *)
        spin1_malloc(sizeof(struct all_to_all));

    // Copy the parameters into the data structure
    address_t params_sdram = *region;
    spin1_memcpy(params, params_sdram, sizeof(struct all_to_all));
    params_sdram = &(params_sdram[sizeof(struct all_to_all) >> 2]);
    log_debug("All to all connector, allow self connections = %u",
            params->allow_self_connections);

    *region = params_sdram;
    return params;
}

void connection_generator_all_to_all_free(void *data) {
    sark_free(data);
}

uint32_t connection_generator_all_to_all_generate(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    log_debug("Generating for %u", pre_neuron_index);

    struct all_to_all *params = (struct all_to_all *) data;

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // Add a connection to this pre-neuron for each post-neuron...
    uint32_t n_conns = 0;
    for (uint32_t i = 0; i < post_slice_count; i++) {

        // ... unless this is a self connection and these are disallowed
        if (!params->allow_self_connections &&
                (pre_neuron_index == (post_slice_start + i))) {
            log_debug("Not generating for post %u", post_slice_start + i);
            continue;
        }
        indices[n_conns++] = i;
    }

    return n_conns;
}
