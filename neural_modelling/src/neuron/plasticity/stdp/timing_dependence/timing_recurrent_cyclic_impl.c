#include "random.h"
#include <string.h>
#include "timing_recurrent_cyclic_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
#define ACCUM_SCALING   10

// Exponential lookup-tables
//uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
//uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];
//uint16_t pre_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];
//uint16_t post_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];

uint16_t pre_exp_dist_lookup_excit[STDP_FIXED_POINT_ONE>>2];
uint16_t post_exp_dist_lookup_excit[STDP_FIXED_POINT_ONE>>2];
uint16_t pre_exp_dist_lookup_excit2[STDP_FIXED_POINT_ONE>>2];
uint16_t post_exp_dist_lookup_excit2[STDP_FIXED_POINT_ONE>>2];
uint16_t pre_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE>>2];
uint16_t post_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE>>2];
uint16_t pre_exp_dist_lookup_inhib2[STDP_FIXED_POINT_ONE>>2];
uint16_t post_exp_dist_lookup_inhib2[STDP_FIXED_POINT_ONE>>2];

uint32_t recurrentSeed[4];

plasticity_params_recurrent_t recurrent_plasticity_params;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *timing_initialise(address_t address) {

    //log_info("timing_initialise: starting");
    //log_info("\tRecurrent dual-FSM STDP Rule");
    //log_info("\tRec-FSM");

    recurrent_plasticity_params.accum_decay_per_ts     = (int32_t) address[0];

    recurrent_plasticity_params.accum_dep_plus_one[0]  = (int32_t) address[1];
    recurrent_plasticity_params.accum_pot_minus_one[0] = (int32_t) address[2];
    recurrent_plasticity_params.pre_window_tc[0]       = (int32_t) address[3];
    recurrent_plasticity_params.post_window_tc[0]      = (int32_t) address[4];

    recurrent_plasticity_params.accum_dep_plus_one[1]  = (int32_t) address[5];
    recurrent_plasticity_params.accum_pot_minus_one[1] = (int32_t) address[6];
    recurrent_plasticity_params.pre_window_tc[1]       = (int32_t) address[7];
    recurrent_plasticity_params.post_window_tc[1]      = (int32_t) address[8];

    recurrent_plasticity_params.accum_dep_plus_one[2]  = (int32_t) address[9];
    recurrent_plasticity_params.accum_pot_minus_one[2] = (int32_t) address[10];
    recurrent_plasticity_params.pre_window_tc[2]       = (int32_t) address[11];
    recurrent_plasticity_params.post_window_tc[2]      = (int32_t) address[12];

    recurrent_plasticity_params.accum_dep_plus_one[3]  = (int32_t) address[13];
    recurrent_plasticity_params.accum_pot_minus_one[3] = (int32_t) address[14];
    recurrent_plasticity_params.pre_window_tc[3]       = (int32_t) address[15];
    recurrent_plasticity_params.post_window_tc[3]      = (int32_t) address[16];

    log_info("Accum decay per TS: %d", (int)(recurrent_plasticity_params.accum_decay_per_ts));
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
        &address[17], STDP_FIXED_POINT_ONE>>2, (int16_t*) &pre_exp_dist_lookup_excit[0]);

    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &post_exp_dist_lookup_excit[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &pre_exp_dist_lookup_excit2[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &post_exp_dist_lookup_excit2[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &pre_exp_dist_lookup_inhib[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &post_exp_dist_lookup_inhib[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &pre_exp_dist_lookup_inhib2[0]);
    lut_address = maths_copy_int16_lut(
        lut_address, STDP_FIXED_POINT_ONE>>2, (int16_t*) &post_exp_dist_lookup_inhib2[0]);

    //log_info("lut_address: %u", lut_address);
    memcpy(recurrentSeed, lut_address, 4 * sizeof(uint32_t));
    log_info("%d %d %d %d", recurrentSeed[0], recurrentSeed[1], recurrentSeed[2], recurrentSeed[3]);
    lut_address += 4;
    validate_mars_kiss64_seed(recurrentSeed);

    log_info("timing_cyclic initialise: completed successfully");

    /*log_info("Pre exp table, I2:");
    for(int u = 0; u< 2048; u+=5) {
        log_info("Idx: %d,   Val: %d", u, pre_exp_dist_lookup_inhib2[u]);
    }
    log_info("Post exp table, I2:");
    for(int u = 0; u< 2048; u+=5) {
        log_info("Idx: %d,   Val: %d", u, post_exp_dist_lookup_inhib2[u]);
    } */
    return lut_address;
}
