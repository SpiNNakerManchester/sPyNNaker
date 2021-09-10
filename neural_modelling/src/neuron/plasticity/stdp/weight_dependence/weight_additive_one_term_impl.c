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
//! \brief Support code for weight_additive_one_term_impl.h
#include "weight_additive_one_term_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;

//! Plasticity multiply shift array, in DTCM
uint32_t *weight_shift;

//! \brief How the configuration data for additive_one_term is laid out in
//!     SDRAM. The layout is an array of these.
typedef struct {
    int32_t min_weight;
    int32_t max_weight;
    int32_t a2_plus;
    int32_t a2_minus;
} additive_one_term_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types,
        UNUSED uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    log_debug("weight_initialise: starting");
    log_debug("\tSTDP additive one-term weight dependence");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    additive_one_term_config_t *config = (additive_one_term_config_t *) address;

    plasticity_weight_region_data_t *dtcm_copy = plasticity_weight_region_data =
            spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (dtcm_copy == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    weight_shift = spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (weight_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    for (uint32_t s = 0; s < n_synapse_types; s++, config++) {
        dtcm_copy[s].min_weight = config->min_weight;
        dtcm_copy[s].max_weight = config->max_weight;
        dtcm_copy[s].a2_plus = config->a2_plus;
        dtcm_copy[s].a2_minus = config->a2_minus;

        // Copy weight shift
        weight_shift[s] = ring_buffer_to_input_buffer_left_shifts[s];

        log_debug("\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d",
                s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
                dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus);
    }
    log_debug("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) config;
}
