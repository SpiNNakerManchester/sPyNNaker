/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Support code for weight_additive_two_term_impl.h
#include "weight_additive_two_term_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;

//! Plasticity multiply shift array, in DTCM
uint32_t *weight_shift;

//! \brief How the configuration data for additive_two_term is laid out in
//!     SDRAM. The layout is an array of these.
typedef struct {
    accum min_weight;
    accum max_weight;
    accum a2_plus;
    accum a2_minus;
    accum a3_plus;
    accum a3_minus;
} additive_two_term_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types,
        UNUSED uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    additive_two_term_config_t *config = (additive_two_term_config_t *) address;

    struct plasticity_weight_region_data_two_term_t *dtcm_copy =
            plasticity_weight_region_data = spin1_malloc(
                    sizeof(struct plasticity_weight_region_data_two_term_t) *
                    n_synapse_types);
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
        dtcm_copy[s].a3_plus = config->a3_plus;
        dtcm_copy[s].a3_minus = config->a3_minus;

        // Copy weight shift
        weight_shift[s] = ring_buffer_to_input_buffer_left_shifts[s];

        log_debug("\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d,"
                " A3+:%d, A3-:%d",
                s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
                dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus,
                dtcm_copy[s].a3_plus, dtcm_copy[s].a3_minus);
    }

    // Return end address of region
    return (address_t) config;
}
