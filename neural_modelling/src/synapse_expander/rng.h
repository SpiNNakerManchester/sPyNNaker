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

#ifndef __RNG_H__
#define __RNG_H__

/**
 * \file
 * \brief Random number generator interface
 */
#include <common-typedefs.h>
#include <random.h>

/**
 * \brief The Random number generator parameters
 */
typedef struct rng {
    mars_kiss64_seed_t seed;
} rng_t;

/**
 * \brief Initialise the random number generator
 * \param[in,out] region: The address to read data from; updated to position
 *                        after data has been read
 * \return An initialised random number generator that can be used with other
 *         functions, or NULL if it couldn't be initialised for any reason
 */
rng_t *rng_init(void **region);

/**
 * \brief Generate a uniformly-distributed random number
 * \param[in] rng: The random number generator instance to generate from
 * \return The number generated between 0 and 0xFFFFFFFF
 */
uint32_t rng_generator(rng_t *rng);

/**
 * \brief Generate an exponentially-distributed random number
 * \param[in] rng: The random number generator instance to use
 * \return The number generated
 */
accum rng_exponential(rng_t *rng);

/**
 * \brief Generate an normally-distributed random number
 * \param[in] rng: The random number generator instance to use
 * \return The number generated
 */
accum rng_normal(rng_t *rng);

/**
 * \brief Finish with a random number generator
 * \param[in] rng: The generator to free
 */
void rng_free(rng_t *rng);

/**
 * \brief An RNG that starts in the same place on every core of the Population
 */
extern rng_t *population_rng;

/**
 * \brief An RNG that is local to the current core
 */
extern rng_t *core_rng;

#endif
