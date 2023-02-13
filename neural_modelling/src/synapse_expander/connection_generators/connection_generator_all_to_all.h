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
 * \dir
 * \brief Connection generators
 * \file
 * \brief All-to-All connection generator implementation
 */

#include <stdbool.h>
#include <synapse_expander/generator_types.h>

//! \brief The parameters to be passed around for this connector
//!
//! Specifies the range of pre- and post-neurons being connected.
struct all_to_all {
    uint32_t allow_self_connections;
};

/**
 * \brief Initialise the all-to-all connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_all_to_all_initialise(void **region) {
    // Allocate the data structure for parameters
    struct all_to_all *params = spin1_malloc(sizeof(struct all_to_all));
    struct all_to_all *params_sdram = *region;

    // Copy the parameters into the data structure
    *params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("All to all connector, allow_self_connections = %u",
            params->allow_self_connections);

    return params;
}

/**
 * \brief Free the all-to-all connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_all_to_all_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief Generate connections with the all-to-all connection generator
 * \param[in] generator: The generator to use to generate connections
 * \param[in] pre_slice_start: The start of the slice of the pre-population
 *                             being generated
 * \param[in] pre_slice_count: The number of neurons in the slice of the
 *                             pre-population being generated
 * \param[in] post_slice_start: The start of the slice of the post-population
 *                              being generated
 * \param[in] post_slice_count: The number of neurons in the slice of the
 *                              post-population being generated
 */
static bool connection_generator_all_to_all_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {

    // Get the actual ranges to generate within
    uint32_t post_start = max(post_slice_start, post_lo);
    uint32_t post_end = min(post_slice_start + post_slice_count - 1, post_hi);

    struct all_to_all *obj = generator;
    for (uint32_t pre = pre_lo; pre <= pre_hi; pre++) {
        for (uint32_t post = post_start; post <= post_end; post++) {
            if (obj->allow_self_connections || pre != post) {
                uint32_t local_post = post - post_slice_start;
                accum weight = param_generator_generate(weight_generator);
                uint16_t delay = rescale_delay(
                        param_generator_generate(delay_generator), timestep_per_delay);
                if (!matrix_generator_write_synapse(matrix_generator, pre, local_post,
                        weight, delay, weight_scale)) {
                    log_error("Matrix not sized correctly!");
                    return false;
                }
            }
        }
    }
    return true;
}
