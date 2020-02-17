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
#include <synapse_expander/generator_types.h>

static initialize_func connection_generator_all_to_all_initialise;
static free_func connection_generator_all_to_all_free;
static generate_connection_func connection_generator_all_to_all_generate;

/**
 *! \brief The parameters to be passed around for this connector
 */
struct all_to_all {
    uint32_t pre_lo;
    uint32_t pre_hi;
    uint32_t post_lo;
    uint32_t post_hi;
    uint32_t allow_self_connections;
};

static void *connection_generator_all_to_all_initialise(address_t *region) {
    // Allocate the data structure for parameters
    struct all_to_all *params = spin1_malloc(sizeof(struct all_to_all));
    struct all_to_all *params_sdram = (void *) *region;

    // Copy the parameters into the data structure
    *params = *params_sdram++;
    *region = (void *) params_sdram;

    log_debug("All to all connector, pre_lo = %u, pre_hi = %u, "
            "post_lo = %u, post_hi = %u, allow_self_connections = %u",
            params->pre_lo, params->pre_hi, params->post_lo, params->post_hi,
            params->allow_self_connections);

    return params;
}

static void connection_generator_all_to_all_free(void *data) {
    sark_free(data);
}

static uint32_t connection_generator_all_to_all_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    log_debug("Generating for %u", pre_neuron_index);

    struct all_to_all *obj = data;

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->pre_lo) ||
            (pre_neuron_index > obj->pre_hi)) {
        return 0;
    }

    // Add a connection to this pre-neuron for each post-neuron...
    uint32_t n_conns = 0;
    for (uint32_t i = 0; i < post_slice_count; i++) {
        // ... unless this is a self connection and these are disallowed
        if (!obj->allow_self_connections &&
                (pre_neuron_index == post_slice_start + i)) {
            log_debug("Not generating for post %u", post_slice_start + i);
            continue;
        }
        // ... or if the value is not in the range of the post-population view
        if ((i + post_slice_start < obj->post_lo) || (i + post_slice_start > obj->post_hi)) {
            continue;
        }
        indices[n_conns++] = i;
    }

    return n_conns;
}
