#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>

struct param_generator_uniform {
    accum low;
    accum high;
};

void *param_generator_uniform_initialize(address_t *region) {
    struct param_generator_uniform *params =
        (struct param_generator_uniform *)
            spin1_malloc(sizeof(struct param_generator_uniform));
    spin1_memcpy(params, *region, sizeof(struct param_generator_uniform));
    *region += sizeof(struct param_generator_uniform) >> 2;
    log_info("Uniform low = %k, high = %k", params->low, params->high);
    return params;
}

void param_generator_uniform_free(void *data) {
    sark_free(data);
}

void param_generator_uniform_generate(
        void *data, uint32_t n_synapses, rng_t rng, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct param_generator_uniform *params =
        (struct param_generator_uniform *) data;
    accum range = params->high - params->low;
    for (uint32_t i = 0; i < n_synapses; i++) {
        values[i] = params->low + (ulrbits(rng_generator(rng)) * range);
    }
}
