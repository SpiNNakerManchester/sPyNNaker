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
//! \brief Support code for weight_multiplicative_impl.h
#include "../../../../meanfield/plasticity/stdp/weight_dependence/weight_multiplicative_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! Global plasticity parameter data array, in DTCM
plasticity_weight_region_data_t *plasticity_weight_region_data;
//! Plasticity multiply shift array, in DTCM
uint32_t *weight_multiply_right_shift;

//! \brief How the configuration data for multiplicative is laid out in SDRAM.
//! The layout is an array of these.
typedef struct {
    int32_t min_weight;
    int32_t max_weight;
    int32_t a2_plus;
    int32_t a2_minus;
} multiplicative_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    log_debug("weight_initialise: starting");
    log_debug("\tSTDP multiplicative weight dependence");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_weight_region_data_t *dtcm_copy = plasticity_weight_region_data =
            spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (dtcm_copy == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    weight_multiply_right_shift =
            spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (weight_multiply_right_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    multiplicative_config_t *config = (multiplicative_config_t *) address;
    for (uint32_t s = 0; s < n_synapse_types; s++, config++) {
        // Copy parameters
        dtcm_copy[s].min_weight = config->min_weight;
        dtcm_copy[s].max_weight = config->max_weight;
        dtcm_copy[s].a2_plus = config->a2_plus;
        dtcm_copy[s].a2_minus = config->a2_minus;

        // Calculate the right shift required to fixed-point multiply weights
        uint32_t shift = weight_multiply_right_shift[s] =
                16 - (ring_buffer_to_input_buffer_left_shifts[s] + 1);

        log_debug("\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d,"
                " Weight multiply right shift:%u",
                s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
                dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus, shift);
    }

    log_debug("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) config;
}
