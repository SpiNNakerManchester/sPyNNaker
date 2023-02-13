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
 * \brief Uniformly distributed random set to boundary parameter generator
 *        implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The parameters that can be copied in from SDRAM
 */
struct uniform_params {
    accum low;
    accum high;
};

/**
 * \brief The data structure to be passed around for this generator.  This
 *        includes the parameters and an RNG.
 */
struct param_generator_uniform {
    struct uniform_params params;
};

/**
 * \brief How to initialise the uniform RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_uniform_initialize(void **region) {
    // Allocate memory for the data
    struct param_generator_uniform *params =
            spin1_malloc(sizeof(struct param_generator_uniform));
    struct uniform_params *params_sdram = *region;

    // Copy the parameters in
    params->params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("Uniform low = %k, high = %k",
            params->params.low, params->params.high);

    return params;
}

/**
 * \brief How to free any data for the uniform RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_uniform_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the uniform RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The generated value
 */
static accum param_generator_uniform_generate(void *generator) {
    // For each index, generate a uniformly distributed value
    struct param_generator_uniform *obj = generator;
    accum range = obj->params.high - obj->params.low;
    return obj->params.low + (ulrbits(rng_generator(core_rng)) * range);
}
