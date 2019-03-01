#include "weight_additive_one_term_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(address_t address, uint32_t n_synapse_types,
                            uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(ring_buffer_to_input_buffer_left_shifts);

    log_debug("weight_initialise: starting");
    log_debug("\tSTDP additive one-term weight dependence");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_weight_region_data_t *config =
            (plasticity_weight_region_data_t *) address;
    plasticity_weight_region_data =
            spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (plasticity_weight_region_data == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    uint32_t s;
    for (s = 0; s < n_synapse_types; s++) {
        plasticity_weight_region_data[s].min_weight = config[s].min_weight;
        plasticity_weight_region_data[s].max_weight = config[s].max_weight;
        plasticity_weight_region_data[s].a2_plus = config[s].a2_plus;
        plasticity_weight_region_data[s].a2_minus = config[s].a2_minus;

        log_debug(
                "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d",
                s, plasticity_weight_region_data[s].min_weight,
                plasticity_weight_region_data[s].max_weight,
                plasticity_weight_region_data[s].a2_plus,
                plasticity_weight_region_data[s].a2_minus);
    }
    log_debug("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) &config[s];
}
