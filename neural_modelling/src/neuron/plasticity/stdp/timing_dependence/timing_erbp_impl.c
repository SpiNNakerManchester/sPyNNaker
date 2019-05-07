#include "timing_erbp_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_plus_lookup[TAU_PLUS_SIZE];
//int16_t tau_minus_lookup[TAU_MINUS_SIZE];
int32_t is_readout;
//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    io_printf(IO_BUF, "timing_initialise: starting\n");
    io_printf(IO_BUF, "\tERBP Learning rule\n");
    // **TODO** assert number of neurons is less than max

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(&address[0], TAU_PLUS_SIZE,
                                                 &tau_plus_lookup[0]);
//    lut_address = maths_copy_int16_lut(lut_address, TAU_MINUS_SIZE,
//                                       &tau_minus_lookup[0]);
    int32_t* plastic_word =  (int32_t*) lut_address;
    is_readout  = *plastic_word++;

    io_printf(IO_BUF, "Is readout core: %u \n", is_readout);

    io_printf(IO_BUF, "timing_initialise: completed successfully\n\n");

    return (address_t) plastic_word;
}
