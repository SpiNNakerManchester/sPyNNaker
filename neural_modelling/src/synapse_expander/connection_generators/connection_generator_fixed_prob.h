/**
 *! \file
 *! \brief Fixed-Probability Connection generator implementation
 */

#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied in from SDRAM
 */
struct fixed_prob_params {
    uint32_t allow_self_connections;
    unsigned long fract probability;
};

/**
 *! \brief The data structure to be passed around for this connector.  This
 *!        includes the parameters and an RNG.
 */
struct fixed_prob {
    struct fixed_prob_params params;
    rng_t rng;
};

void *connection_generator_fixed_prob_initialise(address_t *region) {

    // Allocate memory for the data
    struct fixed_prob *params = (struct fixed_prob *)
        spin1_malloc(sizeof(struct fixed_prob));

    // Copy the parameters in
    address_t params_sdram = *region;
    spin1_memcpy(
        &(params->params), params_sdram, sizeof(struct fixed_prob_params));
    params_sdram = &(params_sdram[sizeof(struct fixed_prob_params) >> 2]);

    // Initialise the RNG for the connector
    params->rng = rng_init(&params_sdram);
    *region = params_sdram;
    log_debug(
        "Fixed Probability Connector, allow self connections = %u, "
        "probability = %k", params->params.allow_self_connections,
        (accum) params->params.probability);
    return params;
}

void connection_generator_fixed_prob_free(void *data) {
    sark_free(data);
}

uint32_t connection_generator_fixed_prob_generate(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    struct fixed_prob *params = (struct fixed_prob *) data;

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // Randomly select connections between each post-neuron
    uint32_t n_conns = 0;
    for (uint32_t i = 0; i < post_slice_count; i++) {

        // Disallow self connections if configured
        if (!params->params.allow_self_connections &&
                (pre_neuron_index == (post_slice_start + i))) {
            continue;
        }

        // Generate a random number
        unsigned long fract value = ulrbits(rng_generator(params->rng));

        // If less than our probability, generate a connection if possible
        if ((value <= params->params.probability) &&
                (n_conns < max_row_length)) {
            indices[n_conns++] = i;
        } else if (n_conns >= max_row_length) {
            log_warning("Row overflow");
        }
    }

    return n_conns;
}
