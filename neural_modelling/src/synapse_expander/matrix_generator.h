#include <stdbool.h>
#include <stdint.h>
#include <common-typedefs.h>

#include "connection_generator.h"
#include "param_generator.h"
#include "rng.h"

typedef struct matrix_generator* matrix_generator_t;

void register_matrix_generators();

matrix_generator_t matrix_generator_init(
    uint32_t hash, address_t *region);

bool matrix_generator_is_static(
    matrix_generator_t matrix_generator);

uint32_t matrix_generator_n_pre_state_words(
    matrix_generator_t matrix_generator);

bool matrix_generator_generate(
    matrix_generator_t generator, address_t synaptic_matrix_address,
    uint32_t address_delta, uint32_t max_n_static, uint32_t max_n_plastic,
    uint32_t max_per_pre_matrix_size, uint32_t synapse_type,
    uint32_t post_slice_start, uint32_t post_slice_count,
    uint32_t pre_slice_start, uint32_t pre_slice_count,
    uint32_t pre_block_start, uint32_t pre_block_count,
    uint32_t words_per_weight, int32_t *weight_scales,
    uint32_t n_synapse_bits, connection_generator_t connection_generator,
    param_generator_t delay_generator, param_generator_t weight_generator,
    rng_t rng, uint16_t *pre_delay_pairs, uint16_t *pair_count);

