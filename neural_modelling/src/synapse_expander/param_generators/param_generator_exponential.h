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
 * \brief Exponentially distributed random parameter generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <random.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The parameters that can be copied in from SDRAM
 */
typedef struct param_generator_exponential_params {
    accum beta;
} param_generator_exponential_params;

/**
 * \brief The data structure to be passed around for this generator.  This
 *        includes the parameters and an RNG.
 */
struct param_generator_exponential {
    param_generator_exponential_params params;
};

/**
 * \brief How to initialise the exponential RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_exponential_initialize(void **region) {
    // Allocate memory for the data
    struct param_generator_exponential *params =
            spin1_malloc(sizeof(struct param_generator_exponential));

    // Copy the parameters in
    param_generator_exponential_params *params_sdram = *region;
    params->params = *params_sdram;
    *region = &params_sdram[1];
    log_debug("exponential beta = %k", params->params.beta);

    return params;
}

/**
 * \brief How to free any data for the exponential RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_exponential_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the exponential RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The value generated
 */
static accum param_generator_exponential_generate(void *generator) {
    // generate an exponentially distributed value
    struct param_generator_exponential *params = generator;
    return rng_exponential(core_rng) * params->params.beta;
}
