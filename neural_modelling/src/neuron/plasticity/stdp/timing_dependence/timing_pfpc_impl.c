#include "timing_pfpc_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
//int16_t exp_sin_lookup[EXP_SIN_LUT_SIZE];
int16_lut *exp_sin_lookup;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

	io_printf(IO_BUF, "timing_pfpc_initialise: starting\n");
    io_printf(IO_BUF, "\tCerebellum PFPC rule\n");

    // Copy LUTs from following memory
//    address_t lut_address = maths_copy_int16_lut_with_size(
//            &address[0], EXP_SIN_LUT_SIZE, &exp_sin_lookup[0]);
    address_t lut_address = address;
    exp_sin_lookup = maths_copy_int16_lut(&lut_address);

    io_printf(IO_BUF, "timing_pfpc_initialise: completed successfully\n");

    return lut_address;
}
