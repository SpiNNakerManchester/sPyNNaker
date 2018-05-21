#include "param_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "param_generators/param_generator_constant.h"
#include "param_generators/param_generator_uniform.h"
#include "param_generators/param_generator_normal.h"
#include "param_generators/param_generator_normal_clipped.h"
#include "param_generators/param_generator_normal_clipped_to_boundary.h"
#include "param_generators/param_generator_exponential.h"

#define N_PARAM_GENERATORS 6

struct param_generator {
    uint32_t index;
    void *data;
};

struct param_generator_info {
    uint32_t hash;
    void* (*initialize)(address_t *region);
    void (*generate)(
        void *data, uint32_t n_synapses, rng_t rng, accum *values);
    void (*free)(void *data);
};

struct param_generator_info param_generators[N_PARAM_GENERATORS];

void register_param_generators() {
    param_generators[0].hash = 0;
    param_generators[0].initialize = param_generator_constant_initialize;
    param_generators[0].generate = param_generator_constant_generate;
    param_generators[0].free = param_generator_constant_free;

    param_generators[1].hash = 1;
    param_generators[1].initialize = param_generator_uniform_initialize;
    param_generators[1].generate = param_generator_uniform_generate;
    param_generators[1].free = param_generator_uniform_free;

    param_generators[2].hash = 2;
    param_generators[2].initialize = param_generator_normal_initialize;
    param_generators[2].generate = param_generator_normal_generate;
    param_generators[2].free = param_generator_normal_free;

    param_generators[3].hash = 3;
    param_generators[3].initialize = param_generator_normal_clipped_initialize;
    param_generators[3].generate = param_generator_normal_clipped_generate;
    param_generators[3].free = param_generator_normal_clipped_free;

    param_generators[4].hash = 4;
    param_generators[4].initialize =
        param_generator_normal_clipped_boundary_initialize;
    param_generators[4].generate =
        param_generator_normal_clipped_boundary_generate;
    param_generators[4].free = param_generator_normal_clipped_boundary_free;

    param_generators[5].hash = 5;
    param_generators[5].initialize = param_generator_exponential_initialize;
    param_generators[5].generate = param_generator_exponential_generate;
    param_generators[5].free = param_generator_exponential_free;
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
    log_error("Param generator with hash %u not found", hash);
    return NULL;
}

void param_generator_generate(
        param_generator_t generator, uint32_t n_indices, rng_t rng,
        accum *values) {
    param_generators[generator->index].generate(
        generator->data, n_indices, rng, values);
}

void param_generator_free(param_generator_t generator) {
    param_generators[generator->index].free(generator->data);
    sark_free(generator);
}
