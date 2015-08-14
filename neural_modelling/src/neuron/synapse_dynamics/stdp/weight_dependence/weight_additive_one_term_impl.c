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
address_t weight_initialise(
        address_t address, uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(ring_buffer_to_input_buffer_left_shifts);

    log_info("weight_initialise: starting");
    log_info("\tSTDP additive one-term weight dependance");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    int32_t *plasticity_word = (int32_t*) address;
    for (uint32_t s = 0; s < SYNAPSE_TYPE_COUNT; s++) {
        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
        plasticity_weight_region_data[s].max_weight = *plasticity_word++;
        plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
        plasticity_weight_region_data[s].a2_minus = *plasticity_word++;

        log_info(
            "\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d",
            s, plasticity_weight_region_data[s].min_weight,
            plasticity_weight_region_data[s].max_weight,
            plasticity_weight_region_data[s].a2_plus,
            plasticity_weight_region_data[s].a2_minus);
    }
    log_info("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) plasticity_word;
}
