#include "timing_pre_only_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
//int16_t tau_plus_lookup[TAU_PLUS_SIZE];
//int16_t tau_minus_lookup[TAU_MINUS_SIZE];
REAL th_v_mem;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\t pre-spike only timing rule");

    int32_t *plasticity_word = (int32_t*) address;
    th_v_mem = *plasticity_word++;

    log_info("threshold: %12.6k", th_v_mem);
    log_info("timing_initialise: completed successfully");

    return plasticity_word;
}
