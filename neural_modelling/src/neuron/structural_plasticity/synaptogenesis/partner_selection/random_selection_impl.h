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
//! \brief Random partner selection rule
#ifndef _RANDOM_SELECTION_IMPL_H_
#define _RANDOM_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>

//! \brief Notifies the rule that a spike has been received
//! \details Not used by this rule
//! \param[in] time: The time that the spike was received at
//! \param[in] spike:
//!     The spike that was received (includes the sending neuron ID)
static inline void partner_spike_received(
        UNUSED uint32_t time, UNUSED spike_t spike) {
}

//! \brief Choose the potential (remote) synaptic partner
//! \param[in] time: The current time
//! \param[out] population_id: The ID of the other population
//! \param[out] sub_population_id: The ID of the subpopulation (corresponds to
//!     remote SpiNNaker core handling the population)
//! \param[out] neuron_id: The ID of the neuron within the subpopulation
//! \param[out] spike: The spike that made this a meaningful choice.
//!     This rule synthesises this.
//! \param[out] m_pop_index: The master population table index.
//! \return True if a choice was made
static inline bool potential_presynaptic_partner(
        UNUSED uint32_t time, uint32_t *restrict population_id,
        uint32_t *restrict sub_population_id, uint32_t *restrict neuron_id,
        spike_t *restrict spike, uint32_t *restrict m_pop_index) {
    extern rewiring_data_t rewiring_data;
    extern pre_pop_info_table_t pre_info;

    uint32_t pop_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
            pre_info.no_pre_pops;
    *population_id = pop_id;
    pre_info_t *preapppop_info = pre_info.prepop_info[pop_id];

    // Select presynaptic sub-population
    uint32_t n_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
            preapppop_info->total_no_atoms;
    uint32_t subpop_id = 0;
    uint32_t sum = 0;
    for (uint32_t i = 0; i < preapppop_info->no_pre_vertices; i++) {
        sum += preapppop_info->key_atom_info[i].n_atoms;
        if (sum >= n_id) {
            subpop_id = i;
            break;
        }
    }
    *sub_population_id = subpop_id;
    key_atom_info_t *kai = &preapppop_info->key_atom_info[subpop_id];

    // Select a presynaptic neuron ID
    n_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * kai->n_atoms;

    *neuron_id = n_id;
    *spike = kai->key | (n_id << kai->n_colour_bits);
    *m_pop_index = kai->m_pop_index;
    return true;
}

#endif // _RANDOM_SELECTION_IMPL_H_
