/*
 * Copyright (c) 2017 The University of Manchester
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
//! \brief Initialisation for timing_vogels_2011_impl.h
#include "timing_vogels_2011_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! Lookup table for pre-computed _&tau;_
int16_lut *tau_lookup;

//! Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

//! How the configuration data for vogels_2011 is laid out in SDRAM.
typedef struct {
    int32_t alpha;
    uint32_t lut_data[];
} vogels_2011_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address) {
    log_info("timing_initialise: starting");
    log_info("\tVogels 2011 timing rule");
    vogels_2011_config_t *config = (vogels_2011_config_t *) address;

    // Copy parameters
    plasticity_trace_region_data.alpha = config->alpha;

    // Copy LUTs from following memory
    address_t lut_address = config->lut_data;
    tau_lookup = maths_copy_int16_lut(&lut_address);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
