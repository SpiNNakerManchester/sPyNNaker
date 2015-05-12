#include "weight_multiplicative_impl.h"
#include "../../../../common/constants.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t
    plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];
uint32_t weight_multiply_right_shift[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Functions
//---------------------------------------

/*! \brief initialised the weight aspect of a STDP rule.
 * \param[in] address: the absolute address in SRAM where the weight parameters
 *  are stored.
 * \param[in] ring_buffer_to_input_buffer_left_shifts: how much a value needs
 * to be shifted in the left direction to support comprises with fixed point
 * arithmetic
 * \param[in] weight_dependence_magic_number the magic number which represents
 * which weight dedependence component this model is expected to use.
 * \return address_t: returns the end of the weight region as an absolute
 * SDRAM memory address.
 */
uint32_t *weight_initialise(
        uint32_t *address, uint32_t *ring_buffer_to_input_buffer_left_shifts,
        uint32_t weight_dependence_magic_number) {

    log_info("weight_initialise: starting");
    log_info("\tSTDP multiplicative weight dependence");

    if (weight_dependence_magic_number !=
        WEIGHT_DEPENDENCY_MULTIPLICATIVE_MAGIC_NUMBER){
        log_error("expected magic number 0x%x, got magic number 0x%x instead.",
                  WEIGHT_DEPENDENCY_MULTIPLICATIVE_MAGIC_NUMBER,
                  weight_dependence_magic_number);
        return (address_t) NULL;
    }

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    int32_t *plasticity_word = (int32_t*) address;
    for (uint32_t s = 0; s < SYNAPSE_TYPE_COUNT; s++) {
        // Copy parameters
        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
        plasticity_weight_region_data[s].max_weight = *plasticity_word++;
        plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
        plasticity_weight_region_data[s].a2_minus = *plasticity_word++;

        // Calculate the right shift required to fixed-point multiply weights
        weight_multiply_right_shift[s] =
                16 - (ring_buffer_to_input_buffer_left_shifts[s] + 1);

        log_info(
            "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d,"
            " Weight multiply right shift:%u",
            s, plasticity_weight_region_data[s].min_weight,
            plasticity_weight_region_data[s].max_weight,
            plasticity_weight_region_data[s].a2_plus,
            plasticity_weight_region_data[s].a2_minus,
            weight_multiply_right_shift[s]);
    }

    log_info("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) plasticity_word;
}
