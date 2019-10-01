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

#ifndef _RANDOM_SELECTION_IMPL_H_
#define _RANDOM_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>

// Include debug header for log_info etc
#include <debug.h>

static inline void partner_spike_received(uint32_t time, spike_t spike) {
    use(time);
    use(spike);
}

extern rewiring_data_t rewiring_data;
extern pre_pop_info_table_t pre_info;

static inline bool potential_presynaptic_partner(
        uint32_t time, uint32_t *population_id, uint32_t *sub_population_id,
        uint32_t *neuron_id, spike_t *spike, uint32_t *m_pop_index) {
    use(time);
    *population_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
                * pre_info.no_pre_pops;
    pre_info_t* preapppop_info =
        pre_info.prepop_info[*population_id];

    // Select presynaptic sub-population
    *neuron_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
                * preapppop_info->total_no_atoms;
    uint32_t sum = 0;
    for (uint32_t i = 0; i < preapppop_info->no_pre_vertices; i++) {
        sum += preapppop_info->key_atom_info[i].n_atoms;
        if (sum >= *neuron_id) {
            *sub_population_id = i;
            break;
        }
    }

    // Select a presynaptic neuron ID
    *neuron_id = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        preapppop_info->key_atom_info[*sub_population_id].n_atoms;

    *spike = preapppop_info->key_atom_info[*sub_population_id].key | *neuron_id;

    *m_pop_index = preapppop_info->key_atom_info[*sub_population_id].m_pop_index;
    return true;
}

#endif // _RANDOM_SELECTION_IMPL_H_
