#include "timing_abbot_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
//int16_t tau_plus_lookup[TAU_PLUS_SIZE];
//int16_t tau_minus_lookup[TAU_MINUS_SIZE];
int16_t tau_P_depression_lookup[TAU_P_SIZE];
int16_t tau_P_facilitation_lookup[TAU_P_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

//    log_info("timing_initialise: starting");
//    log_info("\tAbbot STP rule");

    // Copy LUTs from following memory
    address_t next_param_address = maths_copy_int16_lut(&address[0],
    		TAU_P_SIZE, &tau_P_depression_lookup[0]);
    // Copy LUTs from following memory
    next_param_address = maths_copy_int16_lut(&next_param_address[0],
    		TAU_P_SIZE, &tau_P_facilitation_lookup[0]);

    // Copy parameters
    // STP_params.stp_type = (int32_t) next_param_address[0]; // now read from synaptic row
//    STP_params.f = (int32_t) next_param_address[1];
//
//    log_info("Parameters: "
//    		"\n \t f = %k",
//			STP_params.f << 4);
    log_info("STP memory initialisation completed successfully");

    return (address_t) next_param_address;
}
