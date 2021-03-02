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
//! \brief Random partner selection rule
#ifndef _RANDOM_SELECTION_IMPL_H_
#define _RANDOM_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>
#include <debug.h>

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

    // Select a presynaptic neuron ID
    n_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
            preapppop_info->key_atom_info[subpop_id].n_atoms;

    *neuron_id = n_id;
    *spike = preapppop_info->key_atom_info[subpop_id].key | n_id;
    *m_pop_index = preapppop_info->key_atom_info[subpop_id].m_pop_index;
    return true;
}

#endif // _RANDOM_SELECTION_IMPL_H_
