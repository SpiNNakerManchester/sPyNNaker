#include "timing_pfpc_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_plus_lookup[TAU_PLUS_SIZE];
int16_t tau_minus_lookup[TAU_MINUS_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

	io_printf(IO_BUF, "timing_pfpc_initialise: starting");
    io_printf(IO_BUF, "\tCerebellum PFPC rule");
    // **TODO** assert number of neurons is less than max

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(&address[0], TAU_PLUS_SIZE,
                                                 &tau_plus_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_MINUS_SIZE,
                                       &tau_minus_lookup[0]);

    io_printf(IO_BUF, "timing_pfpc_initialise: completed successfully");

    return lut_address;
}
