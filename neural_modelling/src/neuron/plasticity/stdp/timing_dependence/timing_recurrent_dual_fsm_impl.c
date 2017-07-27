#include "timing_recurrent_dual_fsm_impl.h"
#include "random.h"

//---------------------------------------
// Globals
//---------------------------------------
#define ACCUM_SCALING   10

// Exponential lookup-tables
uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];
uint16_t pre_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];
uint16_t post_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];

uint32_t recurrentSeed[4];

plasticity_params_recurrent_t recurrent_plasticity_params;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\tRecurrent dual-FSM STDP Rule");

    recurrent_plasticity_params.accum_decay_per_ts     = (int32_t) address[0];
    recurrent_plasticity_params.accum_dep_plus_one[0]  = (int32_t) address[1];
    recurrent_plasticity_params.accum_pot_minus_one[0] = (int32_t) address[2];
    recurrent_plasticity_params.pre_window_tc[0]       = (int32_t) address[3];
    recurrent_plasticity_params.post_window_tc[0]      = (int32_t) address[4];
    recurrent_plasticity_params.accum_dep_plus_one[1]  = (int32_t) address[5];
    recurrent_plasticity_params.accum_pot_minus_one[1] = (int32_t) address[6];
    recurrent_plasticity_params.pre_window_tc[1]       = (int32_t) address[7];
    recurrent_plasticity_params.post_window_tc[1]      = (int32_t) address[8];

    log_info("Accum decay per TS: %d", (int)(recurrent_plasticity_params.accum_decay_per_ts>>ACCUM_SCALING));
    log_info("Thresh dep excit: %d", recurrent_plasticity_params.accum_dep_plus_one[0]-1);
    log_info("Thresh pot excit: %d", recurrent_plasticity_params.accum_pot_minus_one[0]+1);
    log_info("Mean pre-win excit:  %d", recurrent_plasticity_params.pre_window_tc[0]);
    log_info("Mean post-win excit: %d", recurrent_plasticity_params.post_window_tc[0]);
    log_info("Thresh dep inhib: %d", recurrent_plasticity_params.accum_dep_plus_one[1]-1);
    log_info("Thresh pot inhib: %d", recurrent_plasticity_params.accum_pot_minus_one[1]+1);
    log_info("Mean pre-win inhib:  %d", recurrent_plasticity_params.pre_window_tc[1]);
    log_info("Mean post-win inhib: %d", recurrent_plasticity_params.post_window_tc[1]);

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(
        &address[9], STDP_FIXED_POINT_ONE, (int16_t*) &pre_exp_dist_lookup[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE, (int16_t*) &post_exp_dist_lookup[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE, (int16_t*) &pre_exp_dist_lookup_inhib[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE, (int16_t*) &post_exp_dist_lookup_inhib[0]);

    memcpy(recurrentSeed, lut_address, 4 * sizeof(uint32_t));
    lut_address += 4;
    validate_mars_kiss64_seed(recurrentSeed);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
