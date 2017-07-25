#include "timing_recurrent_fixed_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

int16_t pre_cdf_lookup[STDP_TRACE_PRE_CDF_SIZE];
int16_t post_cdf_lookup[STDP_TRACE_POST_CDF_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\tRecurrent stochastic STDP rule");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_trace_region_data.accumulator_depression_plus_one =
        (int32_t) address[0];
    plasticity_trace_region_data.accumulator_potentiation_minus_one =
        (int32_t) address[1];

    log_info(
        "\tAccumulator depression=%d, Accumulator potentiation=%d",
        plasticity_trace_region_data.accumulator_depression_plus_one - 1,
        plasticity_trace_region_data.accumulator_potentiation_minus_one + 1);

    // Copy LUTs from following memory
    // **HACK** these aren't actually int16_t-based but this function will still
    // work fine
    address_t lut_address = maths_copy_int16_lut(
        &address[2], STDP_FIXED_POINT_ONE, (int16_t*) &pre_cdf_lookup[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE, (int16_t*) &post_cdf_lookup[0]);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
