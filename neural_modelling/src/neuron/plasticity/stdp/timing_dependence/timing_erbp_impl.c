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

    int32_t is_readout = (int32_t) address[0];

    // Copy LUTs from following memory
    address_t lut_address = &address[1]; //(address_t) plasticity_word++;

    tau_plus_lookup = maths_copy_int16_lut(&lut_address);

    io_printf(IO_BUF, "lut size: %d\n", tau_plus_lookup->size);
    io_printf(IO_BUF, "lut shift: %d\n", tau_plus_lookup->shift);


    io_printf(IO_BUF, "is readout = %u\n", is_readout);


    io_printf(IO_BUF, "timing_initialise: completed successfully\n\n");

    return lut_address;
}
