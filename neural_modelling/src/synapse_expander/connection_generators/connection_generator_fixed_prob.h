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
 * \brief Fixed-Probability Connection generator implementation
 */

#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

// Eclipse does *NOT* like this type!
typedef unsigned long fract probability_t;

//! The parameters that can be copied in from SDRAM
struct fixed_prob_params {
    uint32_t allow_self_connections;
    probability_t probability;
};

/**
 * \brief The data structure to be passed around for this connector.
 *
 * This includes the parameters and an RNG.
 */
struct fixed_prob {
    struct fixed_prob_params params;
};

/**
 * \brief Initialise the fixed-probability connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_fixed_prob_initialise(void **region) {
    // Allocate memory for the data
    struct fixed_prob *obj = spin1_malloc(sizeof(struct fixed_prob));

    // Copy the parameters in
    struct fixed_prob_params *params_sdram = *region;
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("Fixed Probability Connector, allow self connections = %u, "
            "probability = %k",
			obj->params.allow_self_connections, (accum) obj->params.probability);
    return obj;
}

/**
 * \brief Free the fixed-probability connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_fixed_prob_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief Generate connections with the fixed-probability connection generator
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
static bool connection_generator_fixed_prob_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {
    struct fixed_prob *obj = generator;

    // Get the actual ranges to generate within
    uint32_t post_start = max(post_slice_start, post_lo);
    uint32_t post_end = min(post_slice_start + post_slice_count - 1, post_hi);

    for (uint32_t pre = pre_lo; pre <= pre_hi; pre++) {
        for (uint32_t post = post_start; post <= post_end; post++) {
            if (pre == post && !obj->params.allow_self_connections) {
                continue;
            }

            // Generate a random number
            probability_t value = ulrbits(rng_generator(core_rng));

            // If less than our probability, generate a connection
            if (value <= obj->params.probability) {
                uint32_t local_post = post - post_slice_start;
                uint16_t weight = rescale_weight(
                        param_generator_generate(weight_generator), weight_scale);
                uint16_t delay = rescale_delay(
                        param_generator_generate(delay_generator), timestep_per_delay);
                if (!matrix_generator_write_synapse(matrix_generator, pre, local_post,
                        weight, delay)) {
                    // Retry not useful here
                    log_warning("Could not add to matrix!");
                }
            }
        }
    }
    return true;
}
