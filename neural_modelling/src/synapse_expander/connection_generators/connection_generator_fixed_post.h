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
 * \brief Fixed-Number-Post (fan-out) Connection generator implementation
 *
 * Each post-neuron is connected to exactly n_pre pre-neurons (chosen at random)
 */

#include <log.h>
#include <synapse_expander/rng.h>

//! The parameters that can be copied from SDRAM.
struct fixed_post_params {
    //! Low index of range of pre-neuron population
    uint32_t pre_lo;
    //! High index of range of pre-neuron population
    uint32_t pre_hi;
    //! Low index of range of post-neuron population
    uint32_t post_lo;
    //! High index of range of post-neuron population
    uint32_t post_hi;
    //! Do we allow self connections?
    uint32_t allow_self_connections;
    //! Do we allow any neuron to be multiply connected by this connector?
    uint32_t with_replacement;
    //! Number of connections (= number of post neurons we care about)
    uint32_t n_post;
    //! Total number of post neurons
    uint32_t n_post_neurons;
};

/**
 * \brief The state of this connection generator.
 *
 * This includes the parameters, and the RNG of the connector.
 */
struct fixed_post {
    //! Parameters read from SDRAM
    struct fixed_post_params params;
    //! Configured random number generator
    rng_t rng;
};

/**
 * \brief Initialise the fixed-post connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_fixed_post_initialise(address_t *region) {
    // Allocate memory for the parameters
    struct fixed_post *obj = spin1_malloc(sizeof(struct fixed_post));

    // Copy the parameters in
    struct fixed_post_params *params_sdram = (void *) *region;
    obj->params = *params_sdram++;
    *region = (void *) params_sdram;

    // Initialise the RNG
    obj->rng = rng_init(region);
    log_debug("Fixed Number Post Connector, pre_lo = %u, pre_hi = %u, "
    		"post_lo = %u, post_hi = %u, allow self connections = %u, "
            "with replacement = %u, n_post = %u, n post neurons = %u",
			obj->params.pre_lo, obj->params.pre_hi,
			obj->params.post_lo, obj->params.post_hi,
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_post,
            obj->params.n_post_neurons);
    return obj;
}

/**
 * \brief Free the fixed-post connection generator
 * \param[in] generator: The data to free
 */
static void connection_generator_fixed_post_free(void *generator) {
    struct fixed_post *obj = generator;
    rng_free(obj->rng);
    sark_free(generator);
}

/**
 * \brief Generates a uniformly-distributed random number
 * \param[in,out] obj: the generator containing the RNG
 * \param[in] range: the (_upper, exclusive_) limit of the range of random
 *      numbers that may be generated. Should be in range 0..65536
 * \return a random integer in the given input range.
 */
static uint32_t post_random_in_range(struct fixed_post *obj, uint32_t range) {
    uint32_t u01 = rng_generator(obj->rng) & 0x00007fff;
    return (u01 * range) >> 15;
}

/**
 * \brief Generate connections with the fixed-post connection generator
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
static uint32_t connection_generator_fixed_post_generate(
        void *generator, UNUSED uint32_t pre_slice_start,
        UNUSED uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    // If there are no connections to be made, return 0
    struct fixed_post *obj = generator;
    if (max_row_length == 0 || obj->params.n_post == 0) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->params.pre_lo) ||
    		(pre_neuron_index > obj->params.pre_hi)) {
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

    // Loop over the full indices array, and only keep indices that are on this
    // post-slice and within the range of the specified post-population view
    uint32_t count_indices = 0;
    for (uint32_t i = 0; i < n_conns; i++) {
        uint32_t j = full_indices[i] + obj->params.post_lo;
        if ((j >= post_slice_start) && (j < post_slice_start + post_slice_count)) {
//        		(j >= obj->params.post_lo) && (j <= obj->params.post_hi)) {
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
