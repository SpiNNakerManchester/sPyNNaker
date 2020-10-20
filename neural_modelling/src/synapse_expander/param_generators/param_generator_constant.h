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
 * \dir
 * \brief Parameter generators
 * \file
 * \brief Constant value parameter generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The data for the constant value generation
 */
struct param_generator_constant {
    accum value;
};

/**
 * \brief How to initialise the constant parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_constant_initialize(address_t *region) {
    // Allocate space for the parameters
    struct param_generator_constant *params =
            spin1_malloc(sizeof(struct param_generator_constant));

    // Read parameters from SDRAM
    struct param_generator_constant *params_sdram = (void *) *region;
    *params = *params_sdram++;
    *region = (void *) params_sdram;
    log_debug("Constant value %k", params->value);
    return params;
}

/**
 * \brief How to free any data for the constant parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_constant_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the constant parameter generator
 * \param[in] generator: The generator to use to generate values
 * \param[in] n_indices: The number of values to generate
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] indices: The \p n_indices post-neuron indices for each connection
 * \param[out] values: An array into which to place the values; will be
 *                     \p n_indices in size
 */
static void param_generator_constant_generate(
        void *generator, uint32_t n_indices, UNUSED uint32_t pre_neuron_index,
        UNUSED uint16_t *indices, accum *values) {
    // Generate a constant for each index
    struct param_generator_constant *params = generator;
    for (uint32_t i = 0; i < n_indices; i++) {
        values[i] = params->value;
    }
}
