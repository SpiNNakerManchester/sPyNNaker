/**
 *! \file
 *! \brief Contant value parameter generator implementation
 */
#include <stdfix.h>
#include <spin1_api.h>

/**
 *! \brief The data for the constant value generation
 */
struct param_generator_constant {
    accum value;
};

void *param_generator_constant_initialize(address_t *region) {

    // Allocate space for the parameters
    struct param_generator_constant *params =
        (struct param_generator_constant *)
            spin1_malloc(sizeof(struct param_generator_constant));

    // Read parameters from SDRAM
    spin1_memcpy(&params->value, *region, sizeof(accum));
    log_debug("Constant value %k", params->value);
    *region += 1;
    return params;
}

void param_generator_constant_free(void *data) {
    sark_free(data);
}

void param_generator_constant_generate(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);

    // Generate a constant for each index
    struct param_generator_constant *params =
        (struct param_generator_constant *) data;
    for (uint32_t i = 0; i < n_synapses; i++) {
        values[i] = params->value;
    }
}
