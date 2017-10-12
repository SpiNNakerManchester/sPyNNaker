#include "timing_pre_only_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
//int16_t tau_plus_lookup[TAU_PLUS_SIZE];
//int16_t tau_minus_lookup[TAU_MINUS_SIZE];
//REAL th_v_mem;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\t pre-spike only timing rule");

    REAL *plasticity_word = (REAL*) address;
    th_v_mem = *plasticity_word++;

    th_ca_up_l = *plasticity_word++;
    th_ca_up_h = *plasticity_word++;
    th_ca_dn_l = *plasticity_word++;
    th_ca_dn_h = *plasticity_word++;

    log_info("threshold: %12.6k", th_v_mem);
    log_info("Ca2 thresholds: %12.6k, %12.6k, %12.6k, %12.6k", th_ca_up_l, th_ca_up_h, th_ca_dn_l, th_ca_dn_h);
    log_info("timing_initialise: completed successfully");

    return plasticity_word;
}
