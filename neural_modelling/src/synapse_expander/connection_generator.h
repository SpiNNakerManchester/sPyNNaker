#include <stdint.h>
#include <common-typedefs.h>
#include "rng.h"

typedef struct connection_generator* connection_generator_t;

void register_connection_generators();

connection_generator_t connection_generator_init(
    uint32_t hash, address_t *region);

void connection_generator_free(connection_generator_t generator);

uint32_t connection_generator_generate(connection_generator_t generator,
    uint32_t pre_block_start, uint32_t pre_block_count, uint32_t pre_idx,
    uint32_t post_start, uint32_t post_count, uint32_t max_indices,
    rng_t rng, uint16_t *indices);
