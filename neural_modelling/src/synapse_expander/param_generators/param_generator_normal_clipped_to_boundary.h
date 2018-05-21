#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <normal.h>

struct param_generator_normal_clipped_boundary {
    accum mu;
    accum sigma;
    accum low;
    accum high;
};

void *param_generator_normal_clipped_boundary_initialize(address_t *region) {
    struct param_generator_normal_clipped_boundary *params =
        (struct param_generator_normal_clipped_boundary *) spin1_malloc(
            sizeof(struct param_generator_normal_clipped_boundary));
    spin1_memcpy(
        params, *region,
        sizeof(struct param_generator_normal_clipped_boundary));
    *region += sizeof(struct param_generator_normal_clipped_boundary) >> 2;
    log_info(
        "normal clipped to boundary mu = %k, sigma = %k, low = %k, high = %k",
        params->mu, params->sigma, params->low, params->high);
    return params;
}

void param_generator_normal_clipped_boundary_free(void *data) {
    sark_free(data);
}

void param_generator_normal_clipped_boundary_generate(
        void *data, uint32_t n_synapses, rng_t rng, accum *values) {
    struct param_generator_normal_clipped_boundary *params =
        (struct param_generator_normal_clipped_boundary *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        accum value = rng_normal(rng);
        values[i] = params->mu + (value * params->sigma);
        if (values[i] < params->low) {
            values[i] = params->low;
        }
        if (values[i] > params->high) {
            values[i] = params->high;
        }
        log_info("Produced %k", values[i]);
    }
}
