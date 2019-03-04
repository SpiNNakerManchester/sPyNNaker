#include "timing_recurrent_fixed_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

typedef struct {
    int32_t accumulator_depression_plus_one;
    int32_t accumulator_potentiation_minus_one;
    uint32_t pre_window_length;
    uint32_t post_window_length;
} fixed_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {
    log_info("timing_initialise: starting");
    log_info("\tRecurrent STDP rule");

    fixed_config_t *config = (fixed_config_t *) address;

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_trace_region_data.accumulator_depression_plus_one =
            config->accumulator_depression_plus_one;
    plasticity_trace_region_data.accumulator_potentiation_minus_one =
            config->accumulator_potentiation_minus_one;
    plasticity_trace_region_data.pre_window_length = config->pre_window_length;
    plasticity_trace_region_data.post_window_length =
            config->post_window_length;

    log_info("\tAccumulator depression=%d, Accumulator potentiation=%d",
            plasticity_trace_region_data.accumulator_depression_plus_one - 1,
            plasticity_trace_region_data.accumulator_potentiation_minus_one + 1);
    log_info("timing_initialise: completed successfully");

    return (address_t) &config[1];
}
