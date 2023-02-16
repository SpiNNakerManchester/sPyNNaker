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
 * \file
 * \brief An implementation of random number generation
 */
#include "rng.h"
#include <spin1_api.h>
#include <normal.h>
#include "common_mem.h"

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
