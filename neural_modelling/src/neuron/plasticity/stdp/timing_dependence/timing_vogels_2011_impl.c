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

#include "timing_vogels_2011_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_lookup[TAU_SIZE];

// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

typedef struct {
    int32_t alpha;
    uint32_t lut[TAU_SIZE];
} vogels_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(address_t address)
{
    log_info("timing_initialise: starting");
    log_info("\tVogels 2011 timing rule");

    vogels_config_t *config = (vogels_config_t *) address;

    // Copy parameters
    plasticity_trace_region_data.alpha = config->alpha;
    // Copy LUTs from following memory
    (void) maths_copy_int16_lut(config->lut, TAU_SIZE, tau_lookup);

    log_info("timing_initialise: completed successfully");

    return (address_t) &config[1];
}
