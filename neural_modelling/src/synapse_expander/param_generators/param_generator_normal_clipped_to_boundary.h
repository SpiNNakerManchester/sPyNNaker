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
    rng_t *rng;
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

    // Initialise the RNG for this generator
    obj->rng = rng_init(region);
    return obj;
}

/**
 * \brief How to free any data for the clamped normal RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_normal_clipped_boundary_free(void *generator) {
    struct param_generator_normal_clipped_boundary *obj = generator;
    rng_free(obj->rng);
    sark_free(generator);
}

/**
 * \brief How to generate values with the clamped normal RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \param[in] n_indices: The number of values to generate
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] indices: The \p n_indices post-neuron indices for each connection
 * \param[out] values: An array into which to place the values; will be
 *                     \p n_indices in size
 */
static void param_generator_normal_clipped_boundary_generate(
        void *generator, uint32_t n_indices, UNUSED uint32_t pre_neuron_index,
        UNUSED uint16_t *indices, accum *values) {
    // For each index, generate a normally distributed value, clipping
    // it to the given boundary
    struct param_generator_normal_clipped_boundary *obj = generator;
    for (uint32_t i = 0; i < n_indices; i++) {
        accum value = rng_normal(obj->rng);
        values[i] = obj->params.mu + (value * obj->params.sigma);
        if (values[i] < obj->params.low) {
            values[i] = obj->params.low;
        }
        if (values[i] > obj->params.high) {
            values[i] = obj->params.high;
        }
    }
}
