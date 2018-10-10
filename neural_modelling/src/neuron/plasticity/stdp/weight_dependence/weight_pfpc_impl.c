#include "weight_multiplicative_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;
uint32_t *weight_multiply_right_shift;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *weight_initialise(uint32_t *address, uint32_t n_synapse_types,
                            uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    log_debug("weight_initialise: starting\n");
    log_debug("\tSTDP multiplicative weight dependence\n");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    int32_t *plasticity_word = (int32_t*) address;
    plasticity_weight_region_data = (plasticity_weight_region_data_t *)
        spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (plasticity_weight_region_data == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    weight_multiply_right_shift = (uint32_t *)
        spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (weight_multiply_right_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    for (uint32_t s = 0; s < n_synapse_types; s++) {
        // Copy parameters
        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
        plasticity_weight_region_data[s].max_weight = *plasticity_word++;
        plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
        plasticity_weight_region_data[s].a2_minus = *plasticity_word++;

        // Calculate the right shift required to fixed-point multiply weights
        weight_multiply_right_shift[s] =
                16 - (ring_buffer_to_input_buffer_left_shifts[s] + 1);

//        log_debug(
        io_printf(IO_BUF,
            "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d,"
            " Weight multiply right shift:%u\n",
            s, plasticity_weight_region_data[s].min_weight,
            plasticity_weight_region_data[s].max_weight,
            plasticity_weight_region_data[s].a2_plus,
            plasticity_weight_region_data[s].a2_minus,
            weight_multiply_right_shift[s]);
    }

    log_debug("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) plasticity_word;
}
