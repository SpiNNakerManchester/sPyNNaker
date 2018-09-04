#include "weight_additive_one_term_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t
    plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(address_t address,
                            uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(ring_buffer_to_input_buffer_left_shifts);

    log_info("weight_initialise: starting");
    log_info("\tSTP Only - no weight change occurring");

    log_info("weight_initialise: completed successfully");

    // Return end address of region
    return address;
}
