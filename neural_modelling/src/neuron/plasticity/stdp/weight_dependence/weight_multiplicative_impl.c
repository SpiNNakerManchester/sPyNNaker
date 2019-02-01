#include "weight_erbp_impl.h"

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
    log_debug("\tSTDP erbp dependence");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    int32_t *plasticity_word = (int32_t*) address;
    plasticity_weight_region_data = (plasticity_weight_region_data_t *)
        spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (plasticity_weight_region_data == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    for (uint32_t s = 0; s < n_synapse_types; s++) {
        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
        plasticity_weight_region_data[s].max_weight = *plasticity_word++;
        plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
        plasticity_weight_region_data[s].a2_minus = *plasticity_word++;

        log_debug(
            "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d",
            s, plasticity_weight_region_data[s].min_weight,
            plasticity_weight_region_data[s].max_weight,
            plasticity_weight_region_data[s].a2_plus,
            plasticity_weight_region_data[s].a2_minus);
    }
    log_debug("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) plasticity_word;
}
