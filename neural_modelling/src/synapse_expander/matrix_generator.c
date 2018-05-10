#include "matrix_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "matrix_generators/matrix_generator_static.h"
#include <delay_extension/delay_extension.h>

#define N_MATRIX_GENERATORS 1
#define MATRIX_GENERATOR_STATIC_HASH 0
#define MATRIX_GENERATOR_PLASTIC_HASH 1
#define MAX_DELAY 16
#define EMPTY_VAL 0xFF
#define MAX_ROW_LENGTH 256

struct matrix_generator {
    uint32_t index;
    void *data;
};

struct matrix_generator_info {
    uint32_t hash;
    void* (*initialize)(address_t *region);
    void (*write_row)(
        address_t synaptic_matrix,
        address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_length, uint32_t max_delayed_row_length,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, int32_t *delays, int32_t *weights);
    void (*free)(void *data);
};

struct matrix_generator_info matrix_generators[N_MATRIX_GENERATORS];

void register_matrix_generators() {
    matrix_generators[0].hash = 0;
    matrix_generators[0].initialize = matrix_generator_static_initialize;
    matrix_generators[0].write_row = matrix_generator_static_write_row;
    matrix_generators[0].free = matrix_generator_static_free;
}

matrix_generator_t matrix_generator_init(uint32_t hash, address_t *in_region) {

    for (uint32_t i = 0; i < N_MATRIX_GENERATORS; i++) {
        if (hash == matrix_generators[i].hash) {

            address_t region = *in_region;
            matrix_generator_t generator = spin1_malloc(
                sizeof(matrix_generator_t));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }
            generator->index = i;
            generator->data = matrix_generators[i].initialize(&region);
            *in_region = region;
            return generator;
        }
    }
    log_error("Matrix generator with hash %u not found", hash);
    return NULL;
}

void matrix_generator_free(matrix_generator_t generator) {
    matrix_generators[generator->index].free(generator->data);
    sark_free(generator);
}

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
        rng_t rng) {

    uint32_t n_connections = 0;
    uint32_t pre_slice_end = pre_slice_start + pre_slice_count;
    for (uint32_t pre_neuron_index = pre_slice_start;
            pre_neuron_index < pre_slice_end; pre_neuron_index++) {

        uint16_t indices[max_row_length];
        uint32_t n_indices = connection_generator_generate(
            connection_generator, pre_slice_start, pre_slice_end,
            pre_neuron_index, post_slice_start, post_slice_count,
            max_row_length, rng, indices);

        // Generate delays for each index
        int32_t delays[n_indices];
        log_debug("\t\t\t\tGenerating delays-------------------------");
        param_generator_generate(
            delay_generator, n_indices, 1, pre_neuron_index, post_slice_start,
            indices, rng, delays);

        // Generate weights for each index
        int32_t weights[n_indices];
        param_generator_generate(
            weight_generator, n_indices, weight_scales[synapse_type],
            pre_neuron_index, post_slice_start, indices, rng, weights);

        // Write row
        matrix_generators[generator->index].write_row(
            synaptic_matrix, delayed_synaptic_matrix,
            pre_slice_count, pre_neuron_index,
            max_row_length, max_delayed_row_length,
            n_synapse_type_bits, n_synapse_index_bits,
            synapse_type, n_indices, indices, delays, weights);

        n_connections += n_indices;
    }
    log_debug("\t\tTotal synapses generated = %u . Done!",
            n_connections);

    return true;
}
