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

#ifndef _SP_STRUCTS_H_
#define _SP_STRUCTS_H_

#include <neuron/plasticity/synapse_dynamics.h>
#include <neuron/synapse_row.h>
#include <random.h>

// Define the formation and elimination params
struct elimination_params;
struct formation_params;

#define IS_CONNECTION_LAT 1

typedef struct post_to_pre_entry {
    uint8_t pop_index;
    uint8_t sub_pop_index;
    uint16_t neuron_index;
} post_to_pre_entry;

//! information per atom
typedef struct {
    uint32_t key;
    uint32_t mask;
    uint32_t n_atoms;
    uint32_t lo_atom;
    uint32_t m_pop_index;
} key_atom_info_t;

//! individual pre-synaptic sub-population information
typedef struct {
    uint16_t no_pre_vertices;
    uint16_t sp_control;
    uint16_t delay_lo;
    uint16_t delay_hi;
    uint32_t weight;
    uint32_t connection_type;
    uint32_t total_no_atoms;
    key_atom_info_t key_atom_info[];
} pre_info_t;

//! table of individual pre-synaptic information
typedef struct {
    uint32_t no_pre_pops;
    pre_info_t **prepop_info;
} pre_pop_info_table_t;

//! parameters of the synaptic rewiring model
typedef struct {
    uint32_t fast;
    uint32_t p_rew;
    uint32_t s_max;
    uint32_t app_no_atoms;
    uint32_t machine_no_atoms;
    uint32_t low_atom;
    uint32_t high_atom;
    // the 2 seeds that are used: shared for sync, local for everything else
    mars_kiss64_seed_t shared_seed;
    mars_kiss64_seed_t local_seed;
    uint32_t no_pre_pops;
} rewiring_data_t;

//! struct representing the current state of rewiring
typedef struct {
    // Seed referenced from rewiring data
    mars_kiss64_seed_t *local_seed;
    // Low atom copied from rewiring data
    uint32_t post_low_atom;
    // what are the currently selecting pre- and post-synaptic neurons
    uint32_t pre_syn_id;
    uint32_t post_syn_id;
    // does the connection already exist
    uint32_t element_exists;
    // information extracted from the post to pre table
    post_to_pre_entry *post_to_pre_table_entry;
    pre_info_t *pre_population_info;
    key_atom_info_t *key_atom_info;
    post_to_pre_entry post_to_pre;
    // offset in synaptic row (if exists)
    uint32_t offset;
    // current delay (if exists)
    uint16_t delay;
    // current weight (if exists)
    uint16_t weight;
    // synapse type
    uint32_t synapse_type;
} current_state_t;

// \!brief unpack the spike into key and identifying information for the neuron;
//         Identify pop, sub-population and low and high atoms
static inline bool sp_structs_find_by_spike(
        pre_pop_info_table_t *pre_pop_info_table, spike_t spike,
        uint32_t *neuron_id, uint32_t *population_id,
        uint32_t *sub_population_id, uint32_t *m_pop_index) {
    // Amazing linear search inc.
    // Loop over all populations
    for (uint32_t i = 0; i < pre_pop_info_table->no_pre_pops; i++) {
        pre_info_t *pre_pop_info = pre_pop_info_table->prepop_info[i];

        // Loop over all sub-populations and check if the KEY matches
        // (with neuron ID masked out)
        for (int j = 0; j < pre_pop_info->no_pre_vertices; j++) {
            key_atom_info_t *kai = &pre_pop_info->key_atom_info[j];
            if ((spike & kai->mask) == kai->key) {
                *population_id = i;
                *sub_population_id = j;
                *neuron_id = spike & ~kai->mask;
                *m_pop_index = kai->m_pop_index;
                return true;
            }
        }
    }
    return false;
}

// \brief Get the sub-population id and sub-population-based neuron id given
//        the population id and the population-based neuron id
static inline bool sp_structs_get_sub_pop_info(
        pre_pop_info_table_t *pre_pop_table_info, uint32_t population_id,
        uint32_t pop_neuron_id, uint32_t *sub_population_id,
        uint32_t *sub_pop_neuron_id, uint32_t *spike) {
    pre_info_t *app_pop_info =
            pre_pop_table_info->prepop_info[population_id];
    uint32_t neuron_id = pop_neuron_id;
    for (uint32_t i = 0; i < app_pop_info->no_pre_vertices; i++) {
        uint32_t n_atoms = app_pop_info->key_atom_info[i].n_atoms;
        if (neuron_id < n_atoms) {
            *sub_population_id = i;
            *sub_pop_neuron_id = neuron_id;
            *spike = app_pop_info->key_atom_info[i].key | neuron_id;
            return true;
        }
        neuron_id -= n_atoms;
    }
    return false;
}

static inline bool sp_structs_remove_synapse(
        current_state_t *current_state, address_t row) {
    if (!synapse_dynamics_remove_neuron(current_state->offset, row)) {
        return false;
    }
    current_state->post_to_pre_table_entry->neuron_index = 0xFFFF;
    return true;
}

static inline bool sp_structs_add_synapse(
        current_state_t *current_state, address_t row) {
    uint32_t appr_scaled_weight = current_state->pre_population_info->weight;

    uint32_t actual_delay;
    uint32_t offset = current_state->pre_population_info->delay_hi -
            current_state->pre_population_info->delay_lo;
    actual_delay = ulrbits(mars_kiss64_seed(*(current_state->local_seed))) *
        offset + current_state->pre_population_info->delay_lo;

    if (!synapse_dynamics_add_neuron(
            current_state->post_syn_id, row, appr_scaled_weight, actual_delay,
            current_state->pre_population_info->connection_type)) {
        return false;
    }

    *(current_state->post_to_pre_table_entry) = current_state->post_to_pre;
    return true;

}

#endif // _SP_STRUCTS_H_
