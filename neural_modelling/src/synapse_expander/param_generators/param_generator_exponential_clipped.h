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
 * \brief Exponentially distributed random parameter generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <random.h>
#include <synapse_expander/rng.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The maximum number of redraws performed before giving up
 */
#define MAX_REDRAWS 1000

/**
 * \brief The parameters that can be copied in from SDRAM
 */
typedef struct param_generator_exponential_clipped_params {
    accum beta;
    accum low;
    accum high;
} param_generator_exponential_clipped_params;

/**
 * \brief The data structure to be passed around for this generator.  This
 *        includes the parameters and an RNG.
 */
struct param_generator_exponential_clipped {
    param_generator_exponential_clipped_params params;
};

/**
 * \brief How to initialise the exponential RNG parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_exponential_clipped_initialize(void **region) {
    // Allocate memory for the data
    struct param_generator_exponential_clipped *params =
            spin1_malloc(sizeof(struct param_generator_exponential_clipped));

    // Copy the parameters in
    param_generator_exponential_clipped_params *params_sdram = *region;
    params->params = *params_sdram;
    *region = &params_sdram[1];
    log_debug("exponential clipped beta = %k, low = %k, high = %k",
    		params->params.beta, params->params.low, params->params.high);

    return params;
}

/**
 * \brief How to free any data for the exponential RNG parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_exponential_clipped_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the exponential RNG parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The value generated
 */
static accum param_generator_exponential_clipped_generate(void *generator) {
    // generate an exponentially distributed value
    struct param_generator_exponential_clipped *obj = generator;
    uint32_t n_draws = 0;
	accum value = 0k;
	do {
		value = rng_normal(core_rng);
		value = value * obj->params.beta;
		n_draws++;
	} while ((value < obj->params.low || value > obj->params.high)
			&& (n_draws < MAX_REDRAWS));
	if (n_draws == MAX_REDRAWS) {
		log_error("Maximum number of redraws (%u) exceeded on clipped exponential "
				"distribution with beta=%k, low=%k, high=%k",
				n_draws, obj->params.beta, obj->params.low,	obj->params.high);
		rt_error(RTE_SWERR);
	}
	return value;
}
