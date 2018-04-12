#include "timing_recurrent_fixed_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\tRecurrent STDP rule");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_trace_region_data.accumulator_depression_plus_one =
        (int32_t) address[0];
    plasticity_trace_region_data.accumulator_potentiation_minus_one =
        (int32_t) address[1];

    plasticity_trace_region_data.pre_window_length = (int32_t) address[2];
    plasticity_trace_region_data.post_window_length = (int32_t) address[3];

    log_info(
        "\tAccumulator depression=%d, Accumulator potentiation=%d",
        plasticity_trace_region_data.accumulator_depression_plus_one - 1,
        plasticity_trace_region_data.accumulator_potentiation_minus_one + 1);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
