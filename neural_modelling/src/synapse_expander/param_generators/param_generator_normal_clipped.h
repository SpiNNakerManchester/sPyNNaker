#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>
#include <synapse_expander/rng.h>

struct param_generator_normal_clipped_params {
    accum mu;
    accum sigma;
    accum low;
    accum high;
};

struct param_generator_normal_clipped {
    struct param_generator_normal_clipped_params params;
    rng_t rng;
};

void *param_generator_normal_clipped_initialize(address_t *region) {
    struct param_generator_normal_clipped *params =
        (struct param_generator_normal_clipped *)
            spin1_malloc(sizeof(struct param_generator_normal_clipped));
    spin1_memcpy(
        &(params->params), *region,
        sizeof(struct param_generator_normal_clipped_params));
    *region += sizeof(struct param_generator_normal_clipped_params) >> 2;
    log_debug(
        "normal clipped mu = %k, sigma = %k, low = %k, high = %k",
        params->params.mu, params->params.sigma, params->params.low,
        params->params.high);
    params->rng = rng_init(region);
    return params;
}

void param_generator_normal_clipped_free(void *data) {
    sark_free(data);
}

void param_generator_normal_clipped_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct param_generator_normal_clipped *params =
        (struct param_generator_normal_clipped *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        do {
            accum value = rng_normal(params->rng);
            values[i] = params->params.mu + (value * params->params.sigma);
        } while (values[i] < params->params.low ||
                values[i] > params->params.high);
    }
}
