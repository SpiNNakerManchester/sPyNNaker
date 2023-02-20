/*
 * Copyright (c) 2015 The University of Manchester
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
//! \brief Support code for weight_additive_two_term_impl.h
#include "weight_additive_two_term_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;

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

//! Plasticity min_weight array, in DTCM
REAL *min_weight;
REAL *min_weight_recip;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types, REAL *min_weights) {
    log_debug("weight_initialise: starting");
    log_debug("\tSTDP additive two-term weight dependance");
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

    min_weight = spin1_malloc(sizeof(REAL) * n_synapse_types);
    if (min_weight == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    min_weight_recip = spin1_malloc(sizeof(REAL) * n_synapse_types);
    if (min_weight_recip == NULL) {
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

        min_weight[s] = min_weights[s];
        min_weight_recip[s] = min_weights[s+n_synapse_types];

        log_debug("\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d, min_weight %k"
                " A3+:%d, A3-:%d",
                s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
                dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus,
                dtcm_copy[s].a3_plus, dtcm_copy[s].a3_minus, min_weight[s]);
    }

    // Return end address of region
    return (address_t) config;
}
