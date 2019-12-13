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
 *! \brief Fixed-Number-Post (fan-out) Connection generator implementation
 *!        Each post-neuron is connected to exactly n_pre pre-neurons (chosen at random)
 */

#include <log.h>
#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied from SDRAM
 */
struct fixed_post_params {
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_post;
    uint32_t n_post_neurons;
};

/**
 *! \brief The data to be passed around.  This includes the parameters, and the
 *!        RNG of the connector
 */
struct fixed_post {
    struct fixed_post_params params;
    rng_t rng;
};

static void *connection_generator_fixed_post_initialise(address_t *region) {
    // Allocate memory for the parameters
    struct fixed_post *obj = spin1_malloc(sizeof(struct fixed_post));

    // Copy the parameters in
    struct fixed_post_params *params_sdram = (void *) *region;
    obj->params = *params_sdram++;
    *region = (void *) params_sdram;

    // Initialise the RNG
    obj->rng = rng_init(region);
    log_debug("Fixed Number Post Connector, allow self connections = %u, "
            "with replacement = %u, n_post = %u, n post neurons = %u",
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_post,
            obj->params.n_post_neurons);
    return obj;
}

static void connection_generator_fixed_post_free(void *data) {
    struct fixed_post *obj = data;
    rng_free(obj->rng);
    sark_free(data);
}

static uint32_t post_random_in_range(struct fixed_post *obj, uint32_t range) {
    uint32_t u01 = rng_generator(obj->rng) & 0x00007fff;
    return (u01 * range) >> 15;
}

static uint32_t connection_generator_fixed_post_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    // If there are no connections to be made, return 0
    struct fixed_post *obj = data;
    if (max_row_length == 0 || obj->params.n_post == 0) {
        return 0;
    }

    // Get how many values can be sampled from
    uint32_t n_values = obj->params.n_post_neurons;
    // Get the number of connections on this row
    uint32_t n_conns = obj->params.n_post;

    log_debug("Generating %u from %u possible synapses", n_conns, n_values);

    uint16_t full_indices[n_conns];
    // Sample from the possible connections in this section n_conns times
    if (obj->params.with_replacement) {
        // Sample them with replacement
        if (obj->params.allow_self_connections) {
            // self connections are allowed so sample
            for (uint32_t i = 0; i < n_conns; i++) {
                full_indices[i] = post_random_in_range(obj, n_values);
            }
        } else {
            // self connections are not allowed (on this slice)
            for (uint32_t i = 0; i < n_conns; i++) {
                // Set j to the disallowed value, then test against it
                uint32_t j;

                do {
                    j = post_random_in_range(obj, n_values);
                } while (j == pre_neuron_index);

                full_indices[i] = j;
            }
        }
    } else {
        // Sample them without replacement using reservoir sampling
        if (obj->params.allow_self_connections) {
            // Self-connections are allowed so do this normally
            for (uint32_t i = 0; i < n_conns; i++) {
                full_indices[i] = i;
            }
            // And now replace values if chosen at random to be replaced
            for (uint32_t i = n_conns; i < n_values; i++) {
                // j = random(0, i) (inclusive)
                uint32_t j = post_random_in_range(obj, i + 1);

                if (j < n_conns) {
                    full_indices[j] = i;
                }
            }
        } else {
            // Self-connections are not allowed
            uint32_t replace_start = n_conns;
            for (uint32_t i = 0; i < n_conns; i++) {
                if (i == pre_neuron_index) {
                    // set to a value not equal to i for now
                    full_indices[i] = n_conns;
                    replace_start = n_conns + 1;
                } else {
                    full_indices[i] = i;
                }
            }
            // And now "replace" values if chosen at random to be replaced
            for (uint32_t i = replace_start; i < n_values; i++) {
                if (i != pre_neuron_index) {
                    // j = random(0, i) (inclusive)
                    uint32_t j = post_random_in_range(obj, i + 1);

                    if (j < n_conns) {
                        full_indices[j] = i;
                    }
                }
            }
        }
    }

    // Loop over the full indices array, and only keep indices on this post-slice
    uint32_t count_indices = 0;
    for (uint32_t i = 0; i < n_conns; i++) {
        uint32_t j = full_indices[i];
        if ((j >= post_slice_start) && (j < post_slice_start + post_slice_count)) {
            indices[count_indices] = j - post_slice_start; // On this slice!
            count_indices++;
        }
    }

    // Double-check for debug purposes
#if 0
    for (unsigned int i = 0; i < count_indices; i++) {
    	log_info("Check: indices[%u] is %u", i, indices[i]);
    }
    log_info("pre_neuron_index is %u count_indices is %u", pre_neuron_index, count_indices);
#endif

    return count_indices;
}
