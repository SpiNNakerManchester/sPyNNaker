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
 *! \brief Uniformly distributed random set to boundary parameter generator
 *!        implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

static initialize_func param_generator_uniform_initialize;
static free_func param_generator_uniform_free;
static generate_param_func param_generator_uniform_generate;

/**
 *! \brief The parameters that can be copied in from SDRAM
 */
struct uniform_params {
    accum low;
    accum high;
};

/**
 *! \brief The data structure to be passed around for this generator.  This
 *!        includes the parameters and an RNG.
 */
struct param_generator_uniform {
    struct uniform_params params;
    rng_t rng;
};

static void *param_generator_uniform_initialize(address_t *region) {
    // Allocate memory for the data
    struct param_generator_uniform *params =
            spin1_malloc(sizeof(struct param_generator_uniform));
    struct uniform_params *params_sdram = (void *) *region;

    // Copy the parameters in
    params->params = *params_sdram++;
    *region = (void *) params_sdram;

    log_debug("Uniform low = %k, high = %k",
            params->params.low, params->params.high);

    // Initialise the RNG for this generator
    params->rng = rng_init(region);
    return params;
}

static void param_generator_uniform_free(void *data) {
    struct param_generator_uniform *obj = data;
    rng_free(obj->rng);
    sark_free(data);
}

static void param_generator_uniform_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);

    // For each index, generate a uniformly distributed value
    struct param_generator_uniform *obj = data;
    accum range = obj->params.high - obj->params.low;
    for (uint32_t i = 0; i < n_synapses; i++) {
        values[i] = obj->params.low + ulrbits(rng_generator(obj->rng)) * range;
    }
}
