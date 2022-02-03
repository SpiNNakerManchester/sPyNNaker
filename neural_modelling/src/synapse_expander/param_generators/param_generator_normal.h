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
 * \brief Normally distributed random parameter generator implementation
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
struct normal_params {
    accum mu;
    accum sigma;
};

/**
 * \brief The data structure to be passed around for this generator.  This
 *        includes the parameters and an RNG.
 */
struct param_generator_normal {
    struct normal_params params;
};

/**
 * \brief How to initialise the normal RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_normal_initialize(void **region) {
    // Allocate memory for the data
    struct param_generator_normal *obj =
            spin1_malloc(sizeof(struct param_generator_normal));
    struct normal_params *params_sdram = *region;

    // Copy the parameters in
    obj->params = *params_sdram;
    *region = &params_sdram[1];

    log_debug("normal mu = %k, sigma = %k",
            obj->params.mu, obj->params.sigma);
    return obj;
}

/**
 * \brief How to free any data for the normal RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_normal_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the normal RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The generated value
 */
static accum param_generator_normal_generate(void *generator) {
    // For each index, generate a normally distributed random value
    struct param_generator_normal *obj = generator;
    return (rng_normal(core_rng) * obj->params.sigma) + obj->params.mu;
}
