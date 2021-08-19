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

//! \file
//! \brief Initialisation for timing_pfister_triplet_impl.h
#include "../../../../meanfield/plasticity/stdp/timing_dependence/timing_pfister_triplet_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
//! Lookup table for &tau;<sup>+</sup> exponential decay
int16_lut *tau_plus_lookup;
//! Lookup table for &tau;<sup>-</sup> exponential decay
int16_lut *tau_minus_lookup;
//! Lookup table for &tau;<sup><i>x</i></sup> exponential decay
int16_lut *tau_x_lookup;
//! Lookup table for &tau;<sup><i>y</i></sup> exponential decay
int16_lut *tau_y_lookup;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {
    log_info("timing_initialise: starting");
    log_info("\tSTDP triplet rule");
    // **TODO** assert number of neurons is less than max

    // Copy LUTs from following memory
    address_t lut_address = address;
    tau_plus_lookup = maths_copy_int16_lut(&lut_address);
    tau_minus_lookup = maths_copy_int16_lut(&lut_address);
    tau_x_lookup = maths_copy_int16_lut(&lut_address);
    tau_y_lookup = maths_copy_int16_lut(&lut_address);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
