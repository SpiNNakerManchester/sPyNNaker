#include <common-typedefs.h>

#include "connection_generator.h"
#include "param_generator.h"
#include "rng.h"

typedef struct matrix_generator* matrix_generator_t;

void register_matrix_generators();

matrix_generator_t matrix_generator_init(
    uint32_t hash, address_t *region);

void matrix_generator_free(matrix_generator_t generator);

bool matrix_generator_generate(
    matrix_generator_t generator,
    address_t synaptic_matrix, address_t delayed_synaptic_matrix,
    uint32_t max_row_length, uint32_t max_delayed_row_length,
    uint32_t n_synapse_type_bits, uint32_t n_synapse_index_bits,
    uint32_t synapse_type, int32_t *weight_scales,
    uint32_t post_slice_start, uint32_t post_slice_count,
    uint32_t pre_slice_start, uint32_t pre_slice_count,
    connection_generator_t connection_generator,
    param_generator_t delay_generator, param_generator_t weight_generator,
    rng_t rng, uint32_t max_stage, accum timestep_per_delay);
