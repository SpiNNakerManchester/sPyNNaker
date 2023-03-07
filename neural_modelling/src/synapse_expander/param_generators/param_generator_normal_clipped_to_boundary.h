/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * \file
 * \brief Normally distributed random set to boundary parameter generator
 *        implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The parameters that can be copied in from SDRAM
 */
struct normal_clipped_boundary_params {
    accum mu;
    accum sigma;
    accum low;
    accum high;
};

/**
 * \brief The data structure to be passed around for this generator.  This
 *        includes the parameters and an RNG.
 */
struct param_generator_normal_clipped_boundary {
    struct normal_clipped_boundary_params params;
};

/**
 * \brief How to initialise the clamped normal RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_normal_clipped_boundary_initialize(void **region) {
    // Allocate memory for the data
    struct param_generator_normal_clipped_boundary *obj =
            spin1_malloc(sizeof(struct param_generator_normal_clipped_boundary));
    struct normal_clipped_boundary_params *params_sdram = *region;

    // Copy the parameters in
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("normal clipped to boundary mu = %k, sigma = %k, low = %k, high = %k",
            obj->params.mu, obj->params.sigma, obj->params.low, obj->params.high);

    return obj;
}

/**
 * \brief How to free any data for the clamped normal RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_normal_clipped_boundary_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the clamped normal RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return the generated value
 */
static accum param_generator_normal_clipped_boundary_generate(void *generator) {
    // Generate a normally distributed value, clipping
    // it to the given boundary
    struct param_generator_normal_clipped_boundary *obj = generator;
    accum value = rng_normal(core_rng);
    value = obj->params.mu + (value * obj->params.sigma);
    if (value < obj->params.low) {
        return obj->params.low;
    }
    if (value > obj->params.high) {
        return obj->params.high;
    }
    return value;
}
