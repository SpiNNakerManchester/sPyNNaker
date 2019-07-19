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

/**
 *! \brief The parameters that can be copied in from SDRAM
 */
struct param_generator_uniform_params {
    accum low;
    accum high;
};

/**
 *! \brief The data structure to be passed around for this generator.  This
 *!        includes the parameters and an RNG.
 */
struct param_generator_uniform {
    struct param_generator_uniform_params params;
    rng_t rng;
};

void *param_generator_uniform_initialize(address_t *region) {

    // Allocate memory for the data
    struct param_generator_uniform *params =
        (struct param_generator_uniform *)
            spin1_malloc(sizeof(struct param_generator_uniform));

    // Copy the parameters in
    spin1_memcpy(
        &(params->params), *region,
        sizeof(struct param_generator_uniform_params));
    *region += sizeof(struct param_generator_uniform_params) >> 2;
    log_debug("Uniform low = %k, high = %k",
        params->params.low, params->params.high);

    // Initialise the RNG for this generator
    params->rng = rng_init(region);
    return params;
}

void param_generator_uniform_free(void *data) {
    struct param_generator_uniform *params =
            (struct param_generator_uniform *) data;
    rng_free(params->rng);
    sark_free(data);
}

void param_generator_uniform_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);

    // For each index, generate a uniformly distributed value
    struct param_generator_uniform *params =
        (struct param_generator_uniform *) data;
    accum range = params->params.high - params->params.low;
    for (uint32_t i = 0; i < n_synapses; i++) {
        values[i] =
            params->params.low + (ulrbits(rng_generator(params->rng)) * range);
    }
}
