#include <stdint.h>
#include <common-typedefs.h>

typedef struct connection_generator* connection_generator_t;

void register_connection_generators();

connection_generator_t connection_generator_init(
    uint32_t hash, address_t *region);

void connection_generator_free(connection_generator_t generator);

uint32_t connection_generator_generate(
    connection_generator_t generator, uint32_t pre_slice_start,
    uint32_t pre_slice_count, uint32_t pre_neuron_index,
    uint32_t post_slice_start, uint32_t post_slice_count,
    uint32_t max_row_length, uint16_t *indices);
