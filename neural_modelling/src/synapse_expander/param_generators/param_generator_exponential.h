#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <random.h>

struct param_generator_exponential {
    accum beta;
};

void *param_generator_exponential_initialize(address_t *region) {
    struct param_generator_exponential *params =
        (struct param_generator_exponential *)
            spin1_malloc(sizeof(struct param_generator_exponential));
    spin1_memcpy(params, *region, sizeof(struct param_generator_exponential));
    *region += sizeof(struct param_generator_exponential) >> 2;
    log_info("exponential beta = %k", params->beta);
    return params;
}

void param_generator_exponential_free(void *data) {
    sark_free(data);
}

void param_generator_exponential_generate(
        void *data, uint32_t n_synapses, rng_t rng, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct param_generator_exponential *params =
        (struct param_generator_exponential *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        accum value = rng_exponential(rng);
        values[i] = value * params->beta;
    }
}
