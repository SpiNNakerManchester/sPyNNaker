/**
 *! \file
 *! \brief Fixed-Total-Number (Multapse) Connection generator implementation
 */

#include <log.h>
#include <synapse_expander/rng.h>

/**
 *! \brief The parameters that can be copied from SDRAM
 */
struct fixed_total_params {
    uint32_t allow_self_connections;
    uint32_t with_replacement;
    uint32_t n_connections;
    uint32_t n_potential_synapses;
};

/**
 *! \brief The data to be passed around.  This includes the parameters, and the
 *!        RNG of the connector
 */
struct fixed_total {
    struct fixed_total_params params;
    rng_t rng;
};

void *connection_generator_fixed_total_initialise(address_t *region) {

    // Allocate memory for the parameters
    struct fixed_total *params = (struct fixed_total *) spin1_malloc(
        sizeof(struct fixed_total));

    // Copy the parameters in
    address_t params_sdram = *region;
    spin1_memcpy(
        &(params->params), params_sdram, sizeof(struct fixed_total_params));
    params_sdram = &(params_sdram[sizeof(struct fixed_total_params) >> 2]);

    // Initialise the RNG
    params->rng = rng_init(&params_sdram);
    *region = params_sdram;
    log_debug(
        "Fixed Total Number Connector, allow self connections = %u, "
        "with replacement = %u, n connections = %u, "
        "n potential connections = %u", params->params.allow_self_connections,
        params->params.with_replacement, params->params.n_connections,
        params->params.n_potential_synapses);
    return params;
}

void connection_generator_fixed_total_free(void *data) {
    sark_free(data);
}

/**
 *! \brief Draw from a binomial distribution i.e. with replacement
 *! \param[in] n The number of times the experiment is run
 *! \param[in] N The number of items in the bag
 *! \param[in] K The number of items that are valid
 *! \param[in] rng The uniform random number generator
 *! \return The number of times a valid item was drawn
 */
static uint32_t binomial(uint32_t n, uint32_t N, uint32_t K, rng_t rng) {
    uint32_t count = 0;
    uint32_t not_K = N - K;
    for (uint32_t i = 0; i < n; i++) {
        unsigned long fract value = ulrbits(rng_generator(rng));
        uint32_t pos = (uint32_t) (value * (K + not_K));
        if (pos < K) {
            count++;
        }
    }
    return count;
}

/**
 * \brief Draw from a hyper-geometric distribution i.e. without replacement
 * \param[in] n The number of times the experiment is run
 * \param[in] N The number of items in the bag at the start
 * \param[in] K The number of valid items in the bag at the start
 * \param[in] rng The uniform random number generator
 * \return The number of times a valid item was drawn
 */
static uint32_t hypergeom(uint32_t n, uint32_t N, uint32_t K, rng_t rng) {
    uint32_t count = 0;
    uint32_t K_remaining = K;
    uint32_t not_K_remaining = N - K;
    for (uint32_t i = 0; i < n; i++) {
        unsigned long fract value = ulrbits(rng_generator(rng));
        uint32_t pos = (uint32_t) (value * (K_remaining + not_K_remaining));
        if (pos < K_remaining) {
            count += 1;
            K_remaining -= 1;
        } else {
            not_K_remaining -= 1;
        }
    }
    return count;
}

uint32_t connection_generator_fixed_total_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);

    // If there are no connections left or none to be made, return 0
    struct fixed_total *params = (struct fixed_total *) data;
    if (max_row_length == 0 || params->params.n_connections == 0) {
        return 0;
    }

    // Work out how many values can be sampled from
    uint32_t n_values = post_slice_count;
    if (!params->params.allow_self_connections
            && pre_neuron_index >= post_slice_start
            && pre_neuron_index < (post_slice_start + post_slice_count)) {
        n_values -= 1;
    }
    uint32_t n_conns = 0;

    // If we're on the last row of the sub-matrix, then all of the remaining
    // sub-matrix connections get allocated to this row
    if (pre_neuron_index == (pre_slice_start + pre_slice_count - 1)) {
        n_conns = params->params.n_connections;

    } else {

        // If with replacement, generate a binomial for this row
        if (params->params.with_replacement) {
            n_conns = binomial(
                params->params.n_connections,
                params->params.n_potential_synapses, n_values,
                params->rng);

        // If without replacement, generate a hyper-geometric for this row
        } else {
            n_conns = hypergeom(
                params->params.n_connections,
                params->params.n_potential_synapses, n_values,
                params->rng);
        }
    }

    // If too many connections, limit
    if (n_conns > max_row_length) {
        if (pre_neuron_index == (pre_slice_start + pre_slice_count - 1)) {
            log_warning(
                "Could not create %u connections", n_conns - max_row_length);
        }
        n_conns = max_row_length;
    }
    log_debug("Generating %u of %u synapses",
        n_conns, params->params.n_connections);

    // Sample from the possible connections in this row n_conns times
    if (params->params.with_replacement) {

        // Sample them with replacement
        for (unsigned int i = 0; i < n_conns; i++) {
            uint32_t u01 = (rng_generator(params->rng) & 0x00007fff);
            uint32_t j = (u01 * post_slice_count) >> 15;
            indices[i] = j;
        }
    } else {

        // Sample them without replacement using reservoir sampling
        for (unsigned int i = 0; i < n_conns; i++) {
            indices[i] = i;
        }
        for (unsigned int i = n_conns; i < post_slice_count; i++) {

            // j = random(0, i) (inclusive)
            const unsigned int u01 = (rng_generator(params->rng) & 0x00007fff);
            const unsigned int j = (u01 * (i + 1)) >> 15;
            if (j < n_conns) {
                indices[j] = i;
            }
        }
    }

    params->params.n_connections -= n_conns;
    params->params.n_potential_synapses -= post_slice_count;

    return n_conns;
}
