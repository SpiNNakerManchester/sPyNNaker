/*
 * Copyright (c) 2017-2021 The University of Manchester
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

#include "timing_pfpc_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_lut *exp_sin_lookup;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {

	io_printf(IO_BUF, "timing_pfpc_initialise: starting\n");
    io_printf(IO_BUF, "\tCerebellum PFPC rule\n");

    // Copy LUTs from following memory
    address_t lut_address = address;
    exp_sin_lookup = maths_copy_int16_lut(&lut_address);

    io_printf(IO_BUF, "timing_pfpc_initialise: completed successfully\n");

    return lut_address;
}
