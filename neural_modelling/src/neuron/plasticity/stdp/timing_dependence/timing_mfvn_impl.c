/*
 * Copyright (c) 2017-2021 The University of Manchester
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

#include "timing_mfvn_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_lut *exp_cos_lookup;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

	io_printf(IO_BUF, "timing_mfvn_initialise: starting\n");
    io_printf(IO_BUF, "\tCerebellum MFVN rule\n");

    // Copy LUTs from following memory
    address_t lut_address = address;
    exp_cos_lookup = maths_copy_int16_lut(&lut_address);

    io_printf(IO_BUF, "Timing_mfvn_initialise: completed successfully\n");

    return lut_address;
}
