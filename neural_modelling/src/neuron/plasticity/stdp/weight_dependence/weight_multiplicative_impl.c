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
//! \brief Support code for weight_multiplicative_impl.h
#include "weight_multiplicative_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
//! Global plasticity parameter data array, in DTCM
plasticity_weight_region_data_t *plasticity_weight_region_data;

//! Plasticity min_weight array, in DTCM
REAL *min_weight;
REAL *min_weight_recip;

//! \brief How the configuration data for multiplicative is laid out in SDRAM.
//! The layout is an array of these.
typedef struct {
    accum min_weight;
    accum max_weight;
    accum a2_plus;
    accum a2_minus;
} multiplicative_config_t;

//---------------------------------------
// Functions
//---------------------------------------

address_t weight_initialise(
        address_t address, uint32_t n_synapse_types, REAL *min_weights) {
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

    multiplicative_config_t *config = (multiplicative_config_t *) address;
    for (uint32_t s = 0; s < n_synapse_types; s++, config++) {
        // Copy parameters
        dtcm_copy[s].min_weight = config->min_weight;
        dtcm_copy[s].max_weight = config->max_weight;
        dtcm_copy[s].a2_plus = config->a2_plus;
        dtcm_copy[s].a2_minus = config->a2_minus;

        min_weight[s] = min_weights[s];
        min_weight_recip[s] = min_weights[s+n_synapse_types];

        log_debug("\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d, min_weight %k",
                s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
                dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus, min_weight[s]);
    }

    // Return end address of region
    return (address_t) config;
}
