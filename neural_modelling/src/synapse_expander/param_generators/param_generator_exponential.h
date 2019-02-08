/**
 *! \file
 *! \brief Exponentially distributed random parameter generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <random.h>
#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied in from SDRAM
 */
struct param_generator_exponential_params {
    accum beta;
};

/**
 *! \brief The data structure to be passed around for this generator.  This
 *!        includes the parameters and an RNG.
 */
struct param_generator_exponential {
    struct param_generator_exponential_params params;
    rng_t rng;
};

void *param_generator_exponential_initialize(address_t *region) {

    // Allocate memory for the data
    struct param_generator_exponential *params =
        (struct param_generator_exponential *)
            spin1_malloc(sizeof(struct param_generator_exponential));

    // Copy the parameters in
    spin1_memcpy(
        (&params->params), *region,
        sizeof(struct param_generator_exponential_params));
    *region += sizeof(struct param_generator_exponential_params) >> 2;
    log_debug("exponential beta = %k", params->params.beta);

    // Initialise the RNG for this generator
    params->rng = rng_init(region);
    return params;
}

void param_generator_exponential_free(void *data) {
    sark_free(data);
}

void param_generator_exponential_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);

    // For each index, generate an exponentially distributed value
    struct param_generator_exponential *params =
        (struct param_generator_exponential *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        accum value = rng_exponential(params->rng);
        values[i] = value * params->params.beta;
    }
}
