#include <common-typedefs.h>
#include "rng.h"

typedef struct param_generator* param_generator_t;

void register_param_generators();

param_generator_t param_generator_init(
    uint32_t hash, address_t *region);

void param_generator_generate(
    param_generator_t generator, uint32_t n_indices, rng_t rng,
    uint32_t pre_neuron_index, uint16_t *indices, accum *values);

void param_generator_free(param_generator_t generator);
