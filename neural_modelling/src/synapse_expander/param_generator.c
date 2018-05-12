#include "param_generator.h"
#include <spin1_api.h>
#include <debug.h>

#define N_PARAM_GENERATORS 0

struct param_generator {
    uint32_t index;
    void *data;
};

struct param_generator_info {
    uint32_t hash;
    void* (*initialize)(address_t *region);
    void (*generate)(
        void *data, uint32_t n_synapses, int32_t scale, rng_t rng,
        int32_t *values);
    void (*free)(void *data);
};

struct param_generator_info param_generators[N_PARAM_GENERATORS];

void register_param_generators() {

    // TODO: Fill in the generators
}

param_generator_t param_generator_init(uint32_t hash, address_t *in_region) {
    for (uint32_t i = 0; i < N_PARAM_GENERATORS; i++) {
        if (hash == param_generators[i].hash) {

            address_t region = *in_region;
            param_generator_t generator = spin1_malloc(
                sizeof(param_generator_t));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }
            generator->index = i;
            generator->data = param_generators[i].initialize(&region);
            *in_region = region;
            return generator;
        }
    }
    log_error("Matrix generator with hash %u not found", hash);
    return NULL;
}

void param_generator_generate(
        param_generator_t generator, uint32_t n_indices, uint32_t scale,
        rng_t rng, int32_t *values) {
    param_generators[generator->index].generate(
        generator->data, n_indices, scale, rng, values);
}

void param_generator_free(param_generator_t generator) {
    param_generators[generator->index].free(generator->data);
    sark_free(generator);
}
