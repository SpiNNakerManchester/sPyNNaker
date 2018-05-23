#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>

struct param_generator_normal_clipped {
    accum mu;
    accum sigma;
    accum low;
    accum high;
};

void *param_generator_normal_clipped_initialize(address_t *region) {
    struct param_generator_normal_clipped *params =
        (struct param_generator_normal_clipped *)
            spin1_malloc(sizeof(struct param_generator_normal_clipped));
    spin1_memcpy(
        params, *region, sizeof(struct param_generator_normal_clipped));
    *region += sizeof(struct param_generator_normal_clipped) >> 2;
    log_info(
        "normal clipped mu = %k, sigma = %k, low = %k, high = %k",
        params->mu, params->sigma, params->low, params->high);
    return params;
}

void param_generator_normal_clipped_free(void *data) {
    sark_free(data);
}

void param_generator_normal_clipped_generate(
        void *data, uint32_t n_synapses, rng_t rng, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct param_generator_normal_clipped *params =
        (struct param_generator_normal_clipped *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        do {
            accum value = rng_normal(rng);
            values[i] = params->mu + (value * params->sigma);
        } while (values[i] < params->low || values[i] > params->high);
        log_info("Produced %k", values[i]);
    }
}
