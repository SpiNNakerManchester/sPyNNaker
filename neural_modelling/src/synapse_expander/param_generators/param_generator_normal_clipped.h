/*
 * Copyright (c) 2017 The University of Manchester
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
 * \brief Normally distributed random, redrawn if out of boundary, parameter
 *        generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The maximum number of redraws performed before giving up
 */
#define MAX_REDRAWS 1000

/**
 * \brief The parameters that can be copied in from SDRAM
 */
struct normal_clipped_params {
    accum mu;
    accum sigma;
    accum low;
    accum high;
};

/**
 * \brief The data structure to be passed around for this generator.  This
 *        includes the parameters and an RNG.
 */
struct param_generator_normal_clipped {
    struct normal_clipped_params params;
};

/**
 * \brief How to initialise the clipped normal RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_normal_clipped_initialize(void **region) {
    // Allocate memory for the data
    struct param_generator_normal_clipped *obj =
            spin1_malloc(sizeof(struct param_generator_normal_clipped));
    struct normal_clipped_params *params_sdram = *region;

    // Copy the parameters in
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("normal clipped mu = %k, sigma = %k, low = %k, high = %k",
            obj->params.mu, obj->params.sigma, obj->params.low,
            obj->params.high);
    return obj;
}

/**
 * \brief How to free any data for the clipped normal RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_normal_clipped_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the clipped normal RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The generated value
 */
static accum param_generator_normal_clipped_generate(void *generator) {
    // For each index, generate a normally distributed random value, redrawing
    // if outside the given range
    struct param_generator_normal_clipped *obj = generator;
    uint32_t n_draws = 0;
    accum value = 0k;
    do {
        value = rng_normal(core_rng);
        value = obj->params.mu + (value * obj->params.sigma);
        n_draws++;
    } while ((value < obj->params.low || value > obj->params.high)
            && (n_draws < MAX_REDRAWS));
    if (n_draws == MAX_REDRAWS) {
        log_error("Maximum number of redraws (%u) exceeded on clipped normal "
                "distribution with mu=%k, sigma=%k, low=%k, high=%k",
                n_draws, obj->params.mu, obj->params.sigma, obj->params.low,
                obj->params.high);
        rt_error(RTE_SWERR);
    }
    return value;
}
