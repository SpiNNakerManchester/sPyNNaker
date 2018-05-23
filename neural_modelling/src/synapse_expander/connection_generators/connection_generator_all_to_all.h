#include <stdbool.h>

struct all_to_all {
    uint32_t allow_self_connections;
};

void *connection_generator_all_to_all_initialise(address_t *region) {
    struct all_to_all *params = (struct all_to_all *)
        spin1_malloc(sizeof(struct all_to_all));
    address_t params_sdram = *region;
    spin1_memcpy(params, params_sdram, sizeof(struct all_to_all));
    params_sdram = &(params_sdram[sizeof(struct all_to_all) >> 2]);
    log_info("All to all connector, allow self connections = %u",
            params->allow_self_connections);

    *region = params_sdram;
    return params;
}

void connection_generator_all_to_all_free(void *data) {
    sark_free(data);
}

uint32_t connection_generator_all_to_all_generate(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, rng_t rng,
        uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);
    use(rng);

    log_info("Generating for %u", pre_neuron_index);

    struct all_to_all *params = (struct all_to_all *) data;

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // Add a connection to this pre-neuron for each post-neuron...
    uint32_t n_conns = 0;
    for (uint32_t i = 0; i < post_slice_count; i++) {

        // ... unless this is a self connection and these are disallowed
        if (!params->allow_self_connections &&
                (pre_neuron_index == (post_slice_start + i))) {
            log_info("Not generating for post %u", post_slice_start + i);
            continue;
        }
        indices[n_conns++] = i;
    }

    return n_conns;
}
