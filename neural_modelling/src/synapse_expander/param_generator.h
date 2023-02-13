/*
 * Copyright (c) 2017-2023 The University of Manchester
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
 * \file
 * \brief Interface for parameter generator
 */
#include <common-typedefs.h>

/**
 * \brief Parameter generator "object"
 */
typedef struct param_generator *param_generator_t;

/**
 * \brief Initialise a specific parameter generator
 * \param[in] hash: The identifier of the generator to initialise
 * \param[in,out] region: The address to read data from; updated to position
 *                        after data has been read
 * \return An initialised parameter generator that can be used with other
 *         functions, or NULL if it couldn't be initialised for any reason
 */
param_generator_t param_generator_init(uint32_t hash, void **region);

/**
 * \brief Generate value with a parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The value generated
 */
accum param_generator_generate(param_generator_t generator);

/**
 * \brief Finish with a parameter generator
 * \param[in] generator: The generator to free
 */
void param_generator_free(param_generator_t generator);
