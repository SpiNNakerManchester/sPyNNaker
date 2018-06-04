#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>

struct param_generator_normal {
    accum mu;
    accum sigma;
};

void *param_generator_normal_initialize(address_t *region) {
    struct param_generator_normal *params =
        (struct param_generator_normal *)
            spin1_malloc(sizeof(struct param_generator_normal));
    spin1_memcpy(params, *region, sizeof(struct param_generator_normal));
    *region += sizeof(struct param_generator_normal) >> 2;
    log_debug("normal mu = %k, sigma = %k", params->mu, params->sigma);
    return params;
}

void param_generator_normal_free(void *data) {
    sark_free(data);
}

void param_generator_normal_generate(
        void *data, uint32_t n_synapses, rng_t rng, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct param_generator_normal *params =
        (struct param_generator_normal *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        accum value = rng_normal(rng);
        values[i] = params->mu + (value * params->sigma);
    }
}
