#include "connection_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "connection_generators/connection_generator_one_to_one.h"
#include "connection_generators/connection_generator_all_to_all.h"
#include "connection_generators/connection_generator_fixed_prob.h"
#include "connection_generators/connection_generator_fixed_total.h"

#define N_CONNECTION_GENERATORS 4

struct connection_generator {
    uint32_t index;
    void *data;
};

struct connection_generator_info {
    uint32_t hash;
    void* (*initialize)(address_t *region);
    uint32_t (*generate)(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices);
    void (*free)(void *data);
};

struct connection_generator_info connection_generators[N_CONNECTION_GENERATORS];

void register_connection_generators() {
    connection_generators[0].hash = 0;
    connection_generators[0].initialize =
        connection_generator_one_to_one_initialise;
    connection_generators[0].generate =
        connection_generator_one_to_one_generate;
    connection_generators[0].free =
        connection_generator_one_to_one_free;

    connection_generators[1].hash = 1;
    connection_generators[1].initialize =
        connection_generator_all_to_all_initialise;
    connection_generators[1].generate =
        connection_generator_all_to_all_generate;
    connection_generators[1].free =
        connection_generator_all_to_all_free;

    connection_generators[2].hash = 2;
    connection_generators[2].initialize =
        connection_generator_fixed_prob_initialise;
    connection_generators[2].generate =
        connection_generator_fixed_prob_generate;
    connection_generators[2].free =
        connection_generator_fixed_prob_free;

    connection_generators[3].hash = 3;
    connection_generators[3].initialize =
        connection_generator_fixed_total_initialise;
    connection_generators[3].generate =
        connection_generator_fixed_total_generate;
    connection_generators[3].free =
        connection_generator_fixed_total_free;
}

connection_generator_t connection_generator_init(
        uint32_t hash, address_t *in_region) {
    for (uint32_t i = 0; i < N_CONNECTION_GENERATORS; i++) {
        if (hash == connection_generators[i].hash) {

            address_t region = *in_region;
            struct connection_generator *generator = spin1_malloc(
                sizeof(struct connection_generator));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }
            generator->index = i;
            generator->data = connection_generators[i].initialize(&region);
            *in_region = region;
            return generator;
        }
    }
    log_error("Connection generator with hash %u not found", hash);
    return NULL;
}

uint32_t connection_generator_generate(
        connection_generator_t generator, uint32_t pre_slice_start,
        uint32_t pre_slice_count, uint32_t pre_neuron_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t max_row_length, uint16_t *indices) {
    return connection_generators[generator->index].generate(
        generator->data, pre_slice_start, pre_slice_count,
        pre_neuron_index, post_slice_start, post_slice_count,
        max_row_length, indices);
}

void connection_generator_free(connection_generator_t generator) {
    connection_generators[generator->index].free(generator->data);
    sark_free(generator);
}
