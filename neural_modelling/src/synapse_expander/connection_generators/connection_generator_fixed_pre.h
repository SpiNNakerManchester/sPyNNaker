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
 * \file
 * \brief Fixed-Number-Pre (fan-in) Connection generator implementation
 *
 * Each post-neuron is connected to exactly n pre-neurons (chosen at random).
 */

#include <log.h>
#include <synapse_expander/rng.h>
#include <stdbool.h>

//! The parameters that can be copied from SDRAM.
struct fixed_pre_params {
    uint32_t pre_lo;
    uint32_t pre_hi;
    uint32_t post_lo;
    uint32_t post_hi;
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_pre;
    uint32_t n_pre_neurons;
};

/**
 * \brief The data to be passed around.
 *
 * This includes the parameters, and the RNG of the connector.
 */
struct fixed_pre {
    struct fixed_pre_params params;
    rng_t *rng;
};

//! Global values across all the fixed-pre connectors in play on this core
struct fixed_pre_globals_t {
    //! An array containing the indices for each column
    void *full_indices;
    //! How many pre-neurons have been processed so far
    uint32_t n_pre_neurons_done;
    //! Whether \p full_indices is in SDRAM
    bool in_sdram;
};
//! Global values across all the fixed-pre connectors in play on this core
static struct fixed_pre_globals_t fixed_pre_globals = {
    NULL, 0, false
};

/**
 * \brief Generates a uniformly-distributed random number
 * \param[in,out] obj: the generator containing the RNG
 * \param[in] range: the (_upper, exclusive_) limit of the range of random
 *      numbers that may be generated. Should be in range 0..65536
 * \return a random integer in the given input range.
 */
static uint32_t pre_random_in_range(struct fixed_pre *obj, uint32_t range) {
    uint32_t u01 = rng_generator(obj->rng) & 0x00007fff;
    return (u01 * range) >> 15;
}

/**
 * \brief Initialise the fixed-pre connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_fixed_pre_initialise(void **region) {
    // Allocate memory for the parameters
    struct fixed_pre *obj = spin1_malloc(sizeof(struct fixed_pre));

    // Copy the parameters in
    struct fixed_pre_params *params_sdram = *region;
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    // Initialise the RNG
    obj->rng = rng_init(region);
    log_debug("Fixed Number Pre Connector parameters: pre_lo = %u, pre_hi = %u, "
            "post_lo = %u, post_hi = %u, allow self connections = %u, "
            "with replacement = %u, n_pre = %u, n pre neurons = %u",
            obj->params.pre_lo, obj->params.pre_hi, obj->params.post_lo, obj->params.post_hi,
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_pre,
            obj->params.n_pre_neurons);

    // Build the array

    // Get how many values can be sampled from
    uint32_t n_values = obj->params.n_pre_neurons;

    // Get the number of connections in each column
    uint32_t n_conns = obj->params.n_pre;

    log_debug("Generating %u from %u possible synapses", n_conns, n_values);

    // The number of columns is the number of post-slices to do the calculation for
    uint32_t n_columns = obj->params.post_hi - obj->params.post_lo + 1;

    // Allocate array for each column (i.e. post-slice on this slice)
    uint16_t (*array)[n_columns][n_conns] =
            spin1_malloc(n_columns * n_conns * sizeof(uint16_t));
    fixed_pre_globals.in_sdram = false;
    if (array == NULL) {
        log_warning("Could not allocate in DTCM, trying SDRAM");
        array = sark_xalloc(sv->sdram_heap,
                n_columns * n_conns * sizeof(uint16_t), 0, ALLOC_LOCK);
        fixed_pre_globals.in_sdram = true;
    }
    if (array == NULL) {
        log_error("Could not allocate array for indices");
        rt_error(RTE_SWERR);
    }

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
                    } while (j == n); // + post_slice_start);

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
                    if (i == n) { // + post_slice_start) {
                        // set to a value not equal to i for now
                        (*array)[n][i] = n_conns;
                        replace_start = n_conns + 1;
                    } else {
                        (*array)[n][i] = i;
                    }
                }
                // And now "replace" values if chosen at random to be replaced
                for (uint32_t i = replace_start; i < n_values; i++) {
                    if (i != n) { // + post_slice_start)) {
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

    fixed_pre_globals.full_indices = array;

    return obj;
}

/**
 * \brief Free the fixed-pre connection generator
 * \param[in] generator: The generator to free
 */
void connection_generator_fixed_pre_free(void *generator) {
    struct fixed_pre *obj = generator;
    rng_free(obj->rng);
    sark_free(generator);
}

/**
 * \brief Generate connections with the fixed-pre connection generator
 * \param[in] generator: The generator to use to generate connections
 * \param[in] pre_slice_start: The start of the slice of the pre-population
 *                             being generated
 * \param[in] pre_slice_count: The number of neurons in the slice of the
 *                             pre-population being generated
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] post_slice_start: The start of the slice of the post-population
 *                              being generated
 * \param[in] post_slice_count: The number of neurons in the slice of the
 *                              post-population being generated
 * \param[in] max_row_length: The maximum number of connections to generate
 * \param[in,out] indices: An array into which the core-relative post-indices
 *                         should be placed.  This will be initialised to be
 *                         \p max_row_length in size
 * \return The number of connections generated
 */
uint32_t connection_generator_fixed_pre_generate(
        void *generator, UNUSED uint32_t pre_slice_start,
        UNUSED uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    // If there are no connections to be made, return 0

    // Don't think that this is necessary, unless the user says 0 for some reason?
    struct fixed_pre *obj = generator;
    if (max_row_length == 0 || obj->params.n_pre == 0) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->params.pre_lo) ||
    		(pre_neuron_index > obj->params.pre_hi)) {
    	return 0;
    }

    // Get the number of connections in each column
    uint32_t n_conns = obj->params.n_pre;

    // The number of columns is the number of post-slices to do the calculation for
    uint32_t n_columns = obj->params.post_hi - obj->params.post_lo + 1;

    fixed_pre_globals.n_pre_neurons_done = 0;

    uint16_t (*array)[n_columns][n_conns] = fixed_pre_globals.full_indices;

    // Loop over the full indices array, only use pre_neuron_index, and
    // only generate for required columns
    uint32_t count_indices = 0;
    for (uint32_t n = 0; n < n_columns; n++) {
    	// Only generate within the post-population view
    	if ((n + obj->params.post_lo >= post_slice_start) &&
    			(n + obj->params.post_lo < (post_slice_start + post_slice_count))) {
    		for (uint32_t i = 0; i < n_conns; i++) {
    			uint32_t j = (*array)[n][i] + obj->params.pre_lo;
    			if (j == pre_neuron_index) {
    			    // The index is the value locally on the slice
    				indices[count_indices] = n + obj->params.post_lo - post_slice_start;
    				count_indices++;
    			}
    		}
        }
    }

    // If all neurons in pre-slice have been done, free memory
    fixed_pre_globals.n_pre_neurons_done++;
    if (fixed_pre_globals.n_pre_neurons_done == obj->params.n_pre_neurons) {
        if (!fixed_pre_globals.in_sdram) {
            sark_free(fixed_pre_globals.full_indices);
        } else {
            sark_xfree(sv->sdram_heap, fixed_pre_globals.full_indices,
                    ALLOC_LOCK);
        }
        fixed_pre_globals.full_indices = NULL;
    }

    return count_indices;
}
