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

#include "timing_pfister_triplet_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_plus_lookup[TAU_PLUS_SIZE];
int16_t tau_minus_lookup[TAU_MINUS_SIZE];
int16_t tau_x_lookup[TAU_X_SIZE];
int16_t tau_y_lookup[TAU_Y_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    log_info("timing_initialise: starting");
    log_info("\tSTDP triplet rule");
    // **TODO** assert number of neurons is less than max

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(&address[0], TAU_PLUS_SIZE,
                                                 &tau_plus_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_MINUS_SIZE,
                                       &tau_minus_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_X_SIZE,
                                       &tau_x_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_Y_SIZE,
                                       &tau_y_lookup[0]);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
