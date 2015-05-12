#include "weight_additive_two_term_impl.h"
#include "../../../../common/constants.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t
    plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t *ring_buffer_to_input_buffer_left_shifts,
        uint32_t weight_dependence_magic_number) {
    use(ring_buffer_to_input_buffer_left_shifts);

    log_info("weight_initialise: starting");
    log_info("\tSTDP additive two-term weight dependance");

    if (weight_dependence_magic_number !=
        WEIGHT_DEPENDENCY_ADDITIVE_TWO_TERM_MAGIC_NUMBER){
        log_error("expected magic number 0x%x, got magic number 0x%x instead.",
                  WEIGHT_DEPENDENCY_ADDITIVE_TWO_TERM_MAGIC_NUMBER,
                  weight_dependence_magic_number);
        return (address_t) NULL;
    }

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    int32_t *plasticity_word = (int32_t*) address;
    for (uint32_t s = 0; s < SYNAPSE_TYPE_COUNT; s++) {
        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
        plasticity_weight_region_data[s].max_weight = *plasticity_word++;
        plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
        plasticity_weight_region_data[s].a2_minus = *plasticity_word++;
        plasticity_weight_region_data[s].a3_plus = *plasticity_word++;
        plasticity_weight_region_data[s].a3_minus = *plasticity_word++;

        log_info(
            "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d,"
            " A3+:%d, A3-:%d",
            s, plasticity_weight_region_data[s].min_weight,
            plasticity_weight_region_data[s].max_weight,
            plasticity_weight_region_data[s].a2_plus,
            plasticity_weight_region_data[s].a2_minus,
            plasticity_weight_region_data[s].a3_plus,
            plasticity_weight_region_data[s].a3_minus);
    }
    log_info("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) plasticity_word;
}
