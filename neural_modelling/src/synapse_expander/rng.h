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

#endif
