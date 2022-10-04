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
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_pre;
};

/**
 * \brief The data to be passed around.
 */
struct fixed_pre {
    struct fixed_pre_params params;
};

/**
 * \brief Generates a uniformly-distributed random number
 * \param[in] rng: the RNG to generate with
 * \param[in] range: the (_upper, exclusive_) limit of the range of random
 *      numbers that may be generated. Should be in range 0..65536
 * \return a random integer in the given input range.
 */
static uint32_t pre_random_in_range(rng_t *rng, uint32_t range) {
    uint32_t u01 = rng_generator(rng) & 0x00007fff;
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

    log_debug("Fixed Number Pre Connector parameters: "
            "allow self connections = %u, "
            "with replacement = %u, n_pre = %u",
            obj->params.allow_self_connections,
            obj->params.with_replacement, obj->params.n_pre);

    return obj;
}

/**
 * \brief Free the fixed-pre connection generator
 * \param[in] generator: The generator to free
 */
void connection_generator_fixed_pre_free(void *generator) {
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
bool connection_generator_fixed_pre_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {
    // Get the actual ranges to generate within
    uint32_t post_start = max(post_slice_start, post_lo);
    uint32_t post_end = min(post_slice_start + post_slice_count - 1, post_hi);

    struct fixed_pre *obj = generator;
    // Get how many values can be sampled from
    uint32_t n_values = pre_hi - pre_lo + 1;
    // Get the number of connections in each column
    uint32_t n_conns = obj->params.n_pre;

    // We have to generate everything for each column, then just take our share,
    // so we use the population_rng here to ensure all cores do the same thing
    for (uint32_t post = post_start; post <= post_end; post++) {
        uint32_t local_post = post - post_slice_start;
        if (obj->params.with_replacement) {
            // If with replacement just repeated pick
            for (uint32_t j = 0; j < n_conns; j++) {
                uint16_t weight = rescale_weight(
                        param_generator_generate(weight_generator), weight_scale);
                uint16_t delay = rescale_delay(
                        param_generator_generate(delay_generator), timestep_per_delay);
                uint32_t pre;
                bool written = false;
                uint32_t n_retries = 0;
                do {
                    pre = pre_random_in_range(core_rng, n_values) + pre_lo;
                    if (obj->params.allow_self_connections || pre != post) {
                        written = matrix_generator_write_synapse(
                                matrix_generator, pre, local_post, weight, delay);
                        n_retries++;
                    }
                } while (!written && n_retries < 10);
                if (!written) {
                    log_error("Couldn't find a row to write to!");
                    return false;
                }
            }
        } else {
            // Without replacement uses reservoir sampling to save space
            uint16_t values[n_conns];
            uint32_t replace_start = n_conns;
            for (uint32_t j = 0; j < n_conns; j++) {
                if (j == post && !obj->params.allow_self_connections) {
                    values[j] = n_conns;
                    replace_start = n_conns + 1;
                } else {
                    values[j] = j + pre_lo;
                }
            }
            for (uint32_t j = replace_start; j < n_values; j++) {
                // r = random(0, j) (inclusive); swap j into array if r
                // is in range
                if (j != post || obj->params.allow_self_connections) {
                    uint32_t r = pre_random_in_range(core_rng, j + 1);
                    if (r < n_conns) {
                        values[r] = j + pre_lo;
                    }
                }
            }
            for (uint32_t j = 0; j < n_conns; j++) {
                uint16_t weight = rescale_weight(
                        param_generator_generate(weight_generator), weight_scale);
                uint16_t delay = rescale_delay(
                        param_generator_generate(delay_generator), timestep_per_delay);
                // Not a lot we can do here!
                if (!matrix_generator_write_synapse(matrix_generator, values[j],
                        local_post, weight, delay)) {
                    log_warning("Could not write to matrix!");
                }
            }
        }
    }
    return true;
}
