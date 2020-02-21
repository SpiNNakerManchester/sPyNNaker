/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "timing_pair_dual_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_lut *tau_lookup;
int16_lut *tau_plus_lookup;
int16_lut *tau_minus_lookup;

// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *timing_initialise(uint32_t* address) {
    log_info("timing_initialise: starting");
    log_info("\tDual timing rule");

    // Copy parameters
    plasticity_trace_region_data.alpha = (int32_t) address[0];

    // Copy LUTs from following memory
    address_t lut_address = &address[1];
    tau_lookup = maths_copy_int16_lut(&lut_address);

    //---------------------------------------------------------------
    //---------------------------------------------------------------
    tau_plus_lookup = maths_copy_int16_lut(&lut_address); //<- probably need to change address
    tau_minus_lookup = maths_copy_int16_lut(&lut_address);
    io_printf(IO_BUF, "tau_plus first value: %d\n", tau_plus_lookup[0]);
    io_printf(IO_BUF, "tau_minus first value: %d\n", tau_minus_lookup[0]);
    io_printf(IO_BUF, "tau first value: %d\n", tau_lookup[0]);
    io_printf(IO_BUF, "alpha: %d\n", plasticity_trace_region_data.alpha);

    //---------------------------------------------------------------
    //---------------------------------------------------------------

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
