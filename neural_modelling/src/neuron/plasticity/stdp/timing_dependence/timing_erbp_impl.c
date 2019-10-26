#include "timing_erbp_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables

int16_lut *tau_plus_lookup;
int32_t is_readout;
//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    io_printf(IO_BUF, "timing_initialise: starting\n");
    io_printf(IO_BUF, "\tERBP Learning rule\n");
    // **TODO** assert number of neurons is less than max

    // Copy LUTs from following memory
//    address_t lut_address = maths_copy_int16_lut(&address[0], TAU_PLUS_SIZE,
//                                                 &tau_plus_lookup[0]);
//    lut_address = maths_copy_int16_lut(lut_address, TAU_MINUS_SIZE,
//                                       &tau_minus_lookup[0]);


    // Copy LUTs from following memory
    address_t lut_address = address;

    tau_plus_lookup = maths_copy_int16_lut(&lut_address);

    io_printf(IO_BUF, "lut size: %d\n", tau_plus_lookup->size);
    io_printf(IO_BUF, "lut shift: %d\n", tau_plus_lookup->shift);
    io_printf(IO_BUF, "lut last val: %d\n", tau_plus_lookup->values[tau_plus_lookup->size - 1]);



    io_printf(IO_BUF, "end of lut = %u\n", lut_address);

//    int32_t* plastic_word =  (int32_t*) lut_address;
    is_readout  = (int32_t) lut_address;

    io_printf(IO_BUF, "Is readout core 1 less: %d \n", is_readout--);
    io_printf(IO_BUF, "Is readout core 2 less : %d \n", is_readout--);

    io_printf(IO_BUF, "timing_initialise: completed successfully\n\n");

    return (address_t)  is_readout++;
}
