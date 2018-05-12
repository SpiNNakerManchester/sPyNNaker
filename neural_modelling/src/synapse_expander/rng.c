#include "rng.h"
#include <random.h>
#include <spin1_api.h>

struct rng {
    mars_kiss64_seed_t seed;
};

rng_t rng_init(address_t *region) {
    struct rng *rng = (struct rng *) spin1_malloc(sizeof(struct rng));
    spin1_memcpy(rng->seed, *region, sizeof(mars_kiss64_seed_t));
    *region += sizeof(mars_kiss64_seed_t) >> 2;
    return rng;
}

uint32_t rng_generator(rng_t rng) {
    return mars_kiss64_seed(rng->seed);
}

void rng_free(rng_t rng) {
    sark_free(rng);
}
