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
    rng_t rng;
};

/**
 * \brief How to initialise the normal RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_normal_initialize(address_t *region) {
    // Allocate memory for the data
    struct param_generator_normal *obj =
            spin1_malloc(sizeof(struct param_generator_normal));
    struct normal_params *params_sdram = (void *) *region;

    // Copy the parameters in
    obj->params = *params_sdram++;
    *region = (void *) params_sdram;

    log_debug("normal mu = %k, sigma = %k",
            obj->params.mu, obj->params.sigma);

    // Initialise the RNG for this generator
    obj->rng = rng_init(region);
    return obj;
}

/**
 * \brief How to free any data for the normal RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_normal_free(void *generator) {
    struct param_generator_normal *obj = generator;
    rng_free(obj->rng);
    sark_free(generator);
}

/**
 * \brief How to generate values with the normal RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \param[in] n_indices: The number of values to generate
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] indices: The \p n_indices post-neuron indices for each connection
 * \param[out] values: An array into which to place the values; will be
 *                     \p n_indices in size
 */
static void param_generator_normal_generate(
        void *generator, uint32_t n_indices, UNUSED uint32_t pre_neuron_index,
        UNUSED uint16_t *indices, accum *values) {
    // For each index, generate a normally distributed random value
    struct param_generator_normal *obj = generator;
    for (uint32_t i = 0; i < n_indices; i++) {
        accum value = rng_normal(obj->rng);
        values[i] = obj->params.mu + (value * obj->params.sigma);
    }
}
