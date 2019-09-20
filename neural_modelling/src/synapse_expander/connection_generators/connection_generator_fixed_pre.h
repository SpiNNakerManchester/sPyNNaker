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
 *! \brief Fixed-Number-Pre (fan-in) Connection generator implementation
 *!        Each post-neuron is connected to exactly n pre-neurons (chosen at random)
 */

#include <log.h>
#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied from SDRAM
 */
struct fixed_pre_params {
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_pre;
    uint32_t n_pre_neurons;
};

/**
 *! \brief The data to be passed around.  This includes the parameters, and the
 *!        RNG of the connector
 */
struct fixed_pre {
    struct fixed_pre_params params;
    rng_t rng;
};

// An array containing the indices for each column
static void *full_indices = NULL;
static uint32_t n_pre_neurons_done;
static uint32_t in_sdram = 0;

static void *connection_generator_fixed_pre_initialise(address_t *region) {
    // Allocate memory for the parameters
    struct fixed_pre *obj = spin1_malloc(sizeof(struct fixed_pre));

    // Copy the parameters in
    struct fixed_pre_params *params_sdram = (void *) *region;
    obj->params = *params_sdram++;
    *region = (void *) params_sdram;

    // Initialise the RNG
    obj->rng = rng_init(region);
    log_debug("Fixed Total Number Connector, allow self connections = %u, "
            "with replacement = %u, n_pre = %u, n pre neurons = %u",
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_pre,
            obj->params.n_pre_neurons);
    return obj;
}

void connection_generator_fixed_pre_free(void *data) {
    struct fixed_pre *obj = data;
    rng_free(obj->rng);
    sark_free(data);
}

static uint32_t pre_random_in_range(struct fixed_pre *obj, uint32_t range) {
    uint32_t u01 = rng_generator(obj->rng) & 0x00007fff;
    return (u01 * range) >> 15;
}

uint32_t connection_generator_fixed_pre_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    // If there are no connections to be made, return 0

    // Don't think that this is necessary, unless the user says 0 for some reason?
    struct fixed_pre *obj = data;
    if (max_row_length == 0 || obj->params.n_pre == 0) {
        return 0;
    }

    // Get how many values can be sampled from
    uint32_t n_values = obj->params.n_pre_neurons;

    // Get the number of connections in this column
    uint32_t n_conns = obj->params.n_pre;

    log_debug("Generating %u from %u possible synapses", n_conns, n_values);

    // The number of columns is the number of post-slices to do the calculation for
    uint32_t n_columns = post_slice_count;

    // If we haven't done so then do the calculations by looping over
    // the post-slices available here
    if (pre_neuron_index == 0) {
        // Ensure the array was freed
        if (full_indices != NULL) {
            log_error("Created out of order!");
            rt_error(RTE_SWERR);
        }

        n_pre_neurons_done = 0;
        // Allocate array for each column (i.e. post-slice on this slice)
        uint16_t (*array)[n_columns][n_conns] =
                spin1_malloc(n_columns * n_conns * sizeof(uint16_t));
        in_sdram = 0;
        if (array == NULL) {
            log_warning("Could not allocate in DTCM, trying SDRAM");
            array = sark_xalloc(sv->sdram_heap,
                    n_columns * n_conns * sizeof(uint16_t), 0, ALLOC_LOCK);
            in_sdram = 1;
        }
        if (array == NULL) {
            log_error("Could not allocate array for indices");
            rt_error(RTE_SWERR);
        }
        full_indices = array;

        // Loop over the columns and fill the full_indices array accordingly
        for (uint32_t n = 0; n < n_columns; n++) {
            // Sample from the possible connections in this column n_conns times
            if (obj->params.with_replacement) {
                // Sample them with replacement
                if (obj->params.allow_self_connections) {
                    // self connections are allowed so sample
                    for (uint32_t i = 0; i < n_conns; i++) {
                        (*array)[n][i] = pre_random_in_range(obj, n_values);
                    }
                } else {
                    // self connections are not allowed (on this slice)
                    for (uint32_t i = 0; i < n_conns; i++) {
                        // Set j to the disallowed value, then test against it
                        uint32_t j;

                        do {
                            j = pre_random_in_range(obj, n_values);
                        } while (j == n + post_slice_start);

                        (*array)[n][i] = j;
                    }
                }
            } else {
                // Sample them without replacement using reservoir sampling
                if (obj->params.allow_self_connections) {
                    // Self-connections are allowed so do this normally
                    for (uint32_t i = 0; i < n_conns; i++) {
                        (*array)[n][i] = i;
                    }
                    // And now replace values if chosen at random to be replaced
                    for (uint32_t i = n_conns; i < n_values; i++) {
                        // j = random(0, i) (inclusive)
                        uint32_t j = pre_random_in_range(obj, i + 1);

                        if (j < n_conns) {
                            (*array)[n][j] = i;
                        }
                    }
                } else {
                    // Self-connections are not allowed
                    uint32_t replace_start = n_conns;
                    for (uint32_t i = 0; i < n_conns; i++) {
                        if (i == n + post_slice_start) {
                            // set to a value not equal to i for now
                            (*array)[n][i] = n_conns;
                            replace_start = n_conns + 1;
                        } else {
                            (*array)[n][i] = i;
                        }
                    }
                    // And now "replace" values if chosen at random to be replaced
                    for (uint32_t i = replace_start; i < n_values; i++) {
                        if (i != (n + post_slice_start)) {
                            // j = random(0, i) (inclusive)
                            uint32_t j = pre_random_in_range(obj, i + 1);

                            if (j < n_conns) {
                                (*array)[n][j] = i;
                            }
                        }
                    }
                }
            }
        }
    }

    uint16_t (*array)[n_columns][n_conns] = full_indices;

    // Loop over the full indices array, and only use pre_neuron_index
    uint32_t count_indices = 0;
    for (uint32_t n = 0; n < n_columns; n++) {
        for (uint32_t i = 0; i < n_conns; i++) {
            uint32_t j = (*array)[n][i];
            if (j == pre_neuron_index) {
                indices[count_indices] = n; // On this slice!
                count_indices++;
            }
        }
    }

    // If all neurons in pre-slice have been done, free memory
    n_pre_neurons_done++;
    if (n_pre_neurons_done == obj->params.n_pre_neurons) {
        if (!in_sdram) {
            sark_free(full_indices);
        } else {
            sark_xfree(sv->sdram_heap, full_indices, ALLOC_LOCK);
        }
        full_indices = NULL;
    }

    return count_indices;
}
