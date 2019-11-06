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

#include "timing_izhikevich_neuromodulation.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_lut *tau_plus_lookup;
int16_lut *tau_minus_lookup;
int16_lut *tau_c_lookup;
int16_lut *tau_d_lookup;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\tSTDP neuromodulated Izhikevich rule");

    // Copy LUTs from following memory
    address_t lut_address = address;

    tau_plus_lookup = maths_copy_int16_lut(&lut_address);
    tau_minus_lookup = maths_copy_int16_lut(&lut_address);
    tau_c_lookup = maths_copy_int16_lut(&lut_address);
    tau_d_lookup = maths_copy_int16_lut(&lut_address);

    log_debug("check LUT sizes (plus, minus, c, d): %u %u %u %u",
    		tau_plus_lookup->size, tau_minus_lookup->size,
			tau_c_lookup->size, tau_d_lookup->size);
    log_debug("check LUT shifts (plus, minus, c, d): %u %u %u %u",
    		tau_plus_lookup->shift, tau_minus_lookup->shift,
			tau_c_lookup->shift, tau_d_lookup->shift);

    log_debug("check LUT early values (plus, minus, c, d): %u %u %u %u %u %u %u %u",
    		tau_plus_lookup->values[0], tau_plus_lookup->values[1],
			tau_minus_lookup->values[0], tau_minus_lookup->values[1],
			tau_c_lookup->values[0], tau_c_lookup->values[1],
			tau_d_lookup->values[0], tau_d_lookup->values[1]);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
