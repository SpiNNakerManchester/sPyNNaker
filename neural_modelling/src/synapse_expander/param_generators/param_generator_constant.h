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
static void *param_generator_constant_initialize(void **region) {
    // Allocate space for the parameters
    struct param_generator_constant *params =
            spin1_malloc(sizeof(struct param_generator_constant));

    // Read parameters from SDRAM
    struct param_generator_constant *params_sdram = *region;
    *params = *params_sdram;
    *region = &params_sdram[1];
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
 * \return The value generated
 */
static accum param_generator_constant_generate(void *generator) {
    // Generate a constant for each index
    struct param_generator_constant *params = generator;
    return params->value;
}
