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
 *! \file
 *! \brief Exponentially distributed random parameter generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <random.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

static initialize_func param_generator_exponential_initialize;
static free_func param_generator_exponential_free;
static generate_param_func param_generator_exponential_generate;

/**
 *! \brief The parameters that can be copied in from SDRAM
 */
typedef struct param_generator_exponential_params {
    accum beta;
} param_generator_exponential_params;

/**
 *! \brief The data structure to be passed around for this generator.  This
 *!        includes the parameters and an RNG.
 */
struct param_generator_exponential {
    param_generator_exponential_params params;
    rng_t rng;
};

static void *param_generator_exponential_initialize(address_t *region) {
    // Allocate memory for the data
    struct param_generator_exponential *params =
            spin1_malloc(sizeof(struct param_generator_exponential));

    // Copy the parameters in
    param_generator_exponential_params *params_sdram = (void *) *region;
    params->params = *params_sdram++;
    *region = (void *) params_sdram;
    log_debug("exponential beta = %k", params->params.beta);

    // Initialise the RNG for this generator
    params->rng = rng_init(region);
    return params;
}

static void param_generator_exponential_free(void *data) {
    struct param_generator_exponential *params = data;
    rng_free(params->rng);
    sark_free(data);
}

static void param_generator_exponential_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);

    // For each index, generate an exponentially distributed value
    struct param_generator_exponential *params = data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        accum value = rng_exponential(params->rng);
        values[i] = value * params->params.beta;
    }
}
