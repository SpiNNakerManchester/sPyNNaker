#include "timing_mfvn_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t exp_sin_lookup[EXP_SIN_LUT_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

	io_printf(IO_BUF, "timing_mfvn_initialise: starting\n");
    io_printf(IO_BUF, "\tCerebellum MFVN rule\n");
    // **TODO** assert number of neurons is less than max

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(&address[0], EXP_SIN_LUT_SIZE,
                                                 &exp_sin_lookup[0]);

    io_printf(IO_BUF, "Timing_mfvn_initialise: completed successfully\n");

    return lut_address;
}
