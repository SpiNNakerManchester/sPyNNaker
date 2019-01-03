#include "random.h"
//#include <string.h>
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
int32_t random_enabled;
REAL v_diff_pot_threshold;

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

    random_enabled = (int32_t) address[17];
    v_diff_pot_threshold = kbits(address[18]); // Can't cast!

    io_printf(IO_BUF,"Accum decay per TS: %d\n", (int)(recurrent_plasticity_params.accum_decay_per_ts));
    io_printf(IO_BUF,"E1 pot thresh: %d\n", recurrent_plasticity_params.accum_pot_minus_one[0]+1);
    io_printf(IO_BUF,"E1 dep thresh: %d\n", recurrent_plasticity_params.accum_dep_plus_one[0]-1);
    io_printf(IO_BUF,"E1 pot tc:  %d\n", recurrent_plasticity_params.pre_window_tc[0]);
    io_printf(IO_BUF,"E1 dep tc: %d\n", recurrent_plasticity_params.post_window_tc[0]);
    io_printf(IO_BUF,"E2 pot thresh: %d\n", recurrent_plasticity_params.accum_pot_minus_one[1]+1);
    io_printf(IO_BUF,"E2 dep thresh: %d\n", recurrent_plasticity_params.accum_dep_plus_one[1]-1);
    io_printf(IO_BUF,"E2 pot tc:  %d\n", recurrent_plasticity_params.pre_window_tc[1]);
    io_printf(IO_BUF,"E2 dep tc: %d\n", recurrent_plasticity_params.post_window_tc[1]);
    io_printf(IO_BUF,"I1 pot thresh: %d\n", recurrent_plasticity_params.accum_pot_minus_one[2]+1);
    io_printf(IO_BUF,"I1 dep thresh: %d\n", recurrent_plasticity_params.accum_dep_plus_one[2]-1);
    io_printf(IO_BUF,"I1 pot tc:  %d\n", recurrent_plasticity_params.pre_window_tc[2]);
    io_printf(IO_BUF,"I1 dep tc: %d\n", recurrent_plasticity_params.post_window_tc[2]);
    io_printf(IO_BUF,"I2 pot thresh: %d\n", recurrent_plasticity_params.accum_pot_minus_one[3]+1);
    io_printf(IO_BUF,"I2 dep thresh: %d\n", recurrent_plasticity_params.accum_dep_plus_one[3]-1);
    io_printf(IO_BUF,"I2 pot tc:  %d\n", recurrent_plasticity_params.pre_window_tc[3]);
    io_printf(IO_BUF,"I2 dep tc: %d\n", recurrent_plasticity_params.post_window_tc[3]);
    io_printf(IO_BUF, "Random enabled: %u\n",random_enabled);
    io_printf(IO_BUF, "v_diff_pot_threshold: %k\n", v_diff_pot_threshold);

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(
        &address[19], STDP_FIXED_POINT_ONE>>2, (int16_t*) &pre_exp_dist_lookup_excit[0]);

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

    memcpy(recurrentSeed, lut_address, 4 * sizeof(uint32_t));
    lut_address += 4;
    validate_mars_kiss64_seed(recurrentSeed);


//    memcpy(random_enabled, lut_address, sizeof(uint32_t));
//    lut_address += 1;


    io_printf(IO_BUF,"timing_cyclic initialise: completed successfully\n\n");

    return lut_address;
}
