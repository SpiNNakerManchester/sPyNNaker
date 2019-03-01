/**
 *! \file
 *! \brief An implementation of random number generation
 */
#include "rng.h"
#include <random.h>
#include <spin1_api.h>
#include <normal.h>

/**
 *! \brief The Random number generator parameters
 */
struct rng {
    mars_kiss64_seed_t seed;
};

rng_t rng_init(address_t *region) {
    const struct rng *params = (struct rng *) *region;
    struct rng *rng = spin1_malloc(sizeof(struct rng));

    *rng = params[0];
    *region = (address_t) &params[1];
    return rng;
}

uint32_t rng_generator(rng_t rng) {
    return mars_kiss64_seed(rng->seed);
}

accum rng_exponential(rng_t rng) {
    return exponential_dist_variate(mars_kiss64_seed, rng->seed);
}

accum rng_normal(rng_t rng) {
    uint32_t random_value = rng_generator(rng);
    return norminv_urt(random_value);
}

void rng_free(rng_t rng) {
    sark_free(rng);
}
