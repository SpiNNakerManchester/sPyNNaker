/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
    //! Do we allow self connections?
    uint32_t allow_self_connections;
    //! Do we allow any neuron to be multiply connected by this connector?
    uint32_t with_replacement;
    //! Number of connections per pre-neuron in total
    uint32_t n_post;
};

/**
 * \brief The state of this connection generator.
 *
 * This includes the parameters, and the RNG of the connector.
 */
struct fixed_post {
    //! Parameters read from SDRAM
    struct fixed_post_params params;
};

/**
 * \brief Initialise the fixed-post connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_fixed_post_initialise(void **region) {
    // Allocate memory for the parameters
    struct fixed_post *obj = spin1_malloc(sizeof(struct fixed_post));

    // Copy the parameters in
    struct fixed_post_params *params_sdram = *region;
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("Fixed Number Post Connector, allow self connections = %u, "
            "with replacement = %u, n_post = %u",
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_post);
    return obj;
}

/**
 * \brief Free the fixed-post connection generator
 * \param[in] generator: The data to free
 */
static void connection_generator_fixed_post_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief Generates a uniformly-distributed random number
 * \param[in] rng: the RNG to generate with
 * \param[in] range: the (_upper, exclusive_) limit of the range of random
 *      numbers that may be generated. Should be in range 0..65536
 * \return a random integer in the given input range.
 */
static uint32_t post_random_in_range(rng_t *rng, uint32_t range) {
    uint32_t u01 = rng_generator(rng) & 0x00007fff;
    return (u01 * range) >> 15;
}

static bool fixed_post_write(uint32_t pre, uint32_t post, accum weight_scale,
        accum timestep_per_delay, param_generator_t weight_generator,
        param_generator_t delay_generator, matrix_generator_t matrix_generator) {
    accum weight = param_generator_generate(weight_generator);
    uint16_t delay = rescale_delay(
            param_generator_generate(delay_generator), timestep_per_delay);
    return matrix_generator_write_synapse(
            matrix_generator, pre, post, weight, delay, weight_scale);
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
static bool connection_generator_fixed_post_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {

    // Get the actual ranges to generate within
    uint32_t post_slice_end = post_slice_start + post_slice_count;

    struct fixed_post *obj = generator;
    // Get how many values can be sampled from
    uint32_t n_values = post_hi - post_lo + 1;
    // Get the number of connections on each row
    uint32_t n_conns = obj->params.n_post;

    // We have to generate everything for each row, then just take our share,
    // so we use the population_rng here to ensure all cores do the same thing
    for (uint32_t pre = pre_lo; pre <= pre_hi; pre++) {
        if (obj->params.with_replacement) {
            // If with replacement just repeated pick
            for (uint32_t j = 0; j < n_conns; j++) {
                uint32_t post;
                do {
                    post = post_random_in_range(population_rng, n_values) + post_lo;
                } while (!obj->params.allow_self_connections && post == pre);
                // We can only use post neurons in range here
                if (post >= post_slice_start && post < post_slice_end) {
                    post -= post_slice_start;
                    if (!fixed_post_write(pre, post, weight_scale, timestep_per_delay,
                            weight_generator, delay_generator, matrix_generator)) {
                        log_error("Matrix not sized correctly!");
                        return false;
                    }
                }
            }
        } else {
            // Without replacement uses reservoir sampling to save space
            uint16_t values[n_conns];
            uint32_t replace_start = n_conns;
            for (uint32_t j = 0; j < n_conns; j++) {
                if (j == pre && !obj->params.allow_self_connections) {
                    values[j] = n_conns;
                    replace_start = n_conns + 1;
                } else {
                    values[j] = j + post_lo;
                }
            }
            for (uint32_t j = replace_start; j < n_values; j++) {
                // r = random(0, j) (inclusive); swap j into array if r
                // is in range
                if (j != pre || obj->params.allow_self_connections) {
                    uint32_t r = post_random_in_range(population_rng, j + 1);
                    if (r < n_conns) {
                        values[r] = j + post_lo;
                    }
                }
            }
            for (uint32_t j = 0; j < n_conns; j++) {
                if (values[j] >= post_slice_start && values[j] < post_slice_end) {
                    uint32_t post = values[j] - post_slice_start;
                    if (!fixed_post_write(pre, post, weight_scale, timestep_per_delay,
                        weight_generator, delay_generator, matrix_generator)) {
                        log_error("Matrix not sized correctly!");
                        return false;
                    }
                }
            }
        }
    }
    return true;
}
