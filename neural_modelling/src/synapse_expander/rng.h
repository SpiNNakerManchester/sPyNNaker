#include <common-typedefs.h>

typedef struct rng* rng_t;

rng_t rng_init(address_t *region);

uint32_t rng_generator(rng_t rng);

void rng_free(rng_t rng);
