#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>
#include <synapse_expander/rng.h>

struct param_generator_normal_params {
    accum mu;
    accum sigma;
};

struct param_generator_normal {
    struct param_generator_normal_params params;
    rng_t rng;
};

void *param_generator_normal_initialize(address_t *region) {
    struct param_generator_normal *params =
        (struct param_generator_normal *)
            spin1_malloc(sizeof(struct param_generator_normal));
    spin1_memcpy(
        &(params->params), *region,
        sizeof(struct param_generator_normal_params));
    *region += sizeof(struct param_generator_normal_params) >> 2;
    log_debug("normal mu = %k, sigma = %k",
        params->params.mu, params->params.sigma);
    params->rng = rng_init(region);
    return params;
}

void param_generator_normal_free(void *data) {
    sark_free(data);
}

void param_generator_normal_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct param_generator_normal *params =
        (struct param_generator_normal *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        accum value = rng_normal(params->rng);
        values[i] = params->params.mu + (value * params->params.sigma);
    }
}
