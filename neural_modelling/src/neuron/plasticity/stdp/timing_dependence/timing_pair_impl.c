/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Initialisation for timing_pair_impl.h
#include "timing_pair_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
//! Lookup table for &tau;<sup>+</sup> exponential decay
int16_lut *tau_plus_lookup;
//! Lookup table for &tau;<sup>-</sup> exponential decay
int16_lut *tau_minus_lookup;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

    // Copy LUTs from following memory
    address_t lut_address = address;
    tau_plus_lookup = maths_copy_int16_lut(&lut_address);
    tau_minus_lookup = maths_copy_int16_lut(&lut_address);

    return lut_address;
}
