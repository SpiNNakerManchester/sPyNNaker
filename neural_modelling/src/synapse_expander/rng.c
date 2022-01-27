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
 * \brief An implementation of random number generation
 */
#include "rng.h"
#include <spin1_api.h>
#include <normal.h>
#include "common_mem.h"

rng_t *rng_init(void **region) {
    rng_t *rng = spin1_malloc(sizeof(rng_t));
    rng_t *params_sdram = *region;
    *rng = *params_sdram;
    *region = &params_sdram[1];
    return rng;
}

uint32_t rng_generator(rng_t *rng) {
    return mars_kiss64_seed(rng->seed);
}

accum rng_exponential(rng_t *rng) {
    return exponential_dist_variate(mars_kiss64_seed, rng->seed);
}

accum rng_normal(rng_t *rng) {
    uint32_t random_value = rng_generator(rng);
    return norminv_urt(random_value);
}

void rng_free(rng_t *rng) {
    sark_free(rng);
}
