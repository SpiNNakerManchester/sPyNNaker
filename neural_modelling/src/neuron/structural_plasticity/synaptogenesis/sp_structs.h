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

//! \dir
//! \brief Structural plasticity through formation and elimination of synapses
//! \file
//! \brief Miscellaneous structures
#ifndef _SP_STRUCTS_H_
#define _SP_STRUCTS_H_

#include <neuron/plasticity/synapse_dynamics.h>
#include <neuron/synapse_row.h>
#include <debug.h>
#include <random.h>

// Define the formation and elimination params
struct elimination_params;
struct formation_params;

//! Flag: Is connection lateral?
#define IS_CONNECTION_LAT 1

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

//! Entry of map from post-connection to pre-connection neural indices
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
    uint32_t with_replacement;
    // the 2 seeds that are used: shared for sync, local for everything else
    mars_kiss64_seed_t shared_seed;
    mars_kiss64_seed_t local_seed;
    uint32_t no_pre_pops;
} rewiring_data_t;

//! struct representing the current state of rewiring
typedef struct {
    //! Seed referenced from rewiring data
    mars_kiss64_seed_t *local_seed;
    //! Low atom copied from rewiring data
    uint32_t post_low_atom;
    // with_replacement copied from rewiring data
    uint32_t with_replacement;
    // what are the currently selecting pre- and post-synaptic neurons
    uint32_t pre_syn_id;
    uint32_t post_syn_id;
    //! does the connection already exist
    uint32_t element_exists;
    // information extracted from the post to pre table
    post_to_pre_entry *post_to_pre_table_entry;
    pre_info_t *pre_population_info;
    key_atom_info_t *key_atom_info;
    post_to_pre_entry post_to_pre;
    //! offset in synaptic row (if exists)
    uint32_t offset;
    //! current delay (if exists)
    uint16_t delay;
    //! current weight (if exists)
    uint16_t weight;
    //! synapse type
    uint32_t synapse_type;
} current_state_t;

//! Get a random unsigned integer up to (but not including) a given maximum
//! \param[in] max The maximum value allowed
//! \param[in] seed The random seed to use
//! \return The generated value
static inline uint32_t rand_int(uint32_t max, mars_kiss64_seed_t seed) {
    return muliulr(max, ulrbits(mars_kiss64_seed(seed)));
}

//! \brief unpack the spike into key and identifying information for the
//!     neuron; Identify pop, sub-population and low and high atoms
//! \param[in] pre_pop_info_table: The prepopulation information table
//! \param[in] spike: The spike to look up the information from
//! \param[out] neuron_id: The ID of the neuron within its population
//! \param[out] population_id: The population ID
//! \param[out] sub_population_id: The ID of the sub-population
//! \param[out] m_pop_index: The master population table index
//! \return True if the information was found.
static inline bool sp_structs_find_by_spike(
        const pre_pop_info_table_t *pre_pop_info_table, spike_t spike,
        uint32_t *restrict neuron_id, uint32_t *restrict population_id,
        uint32_t *restrict sub_population_id, uint32_t *restrict m_pop_index) {
    // Amazing linear search inc.
    // Loop over all populations
    for (uint32_t i = 0; i < pre_pop_info_table->no_pre_pops; i++) {
        const pre_info_t *pre_pop_info = pre_pop_info_table->prepop_info[i];

        // Loop over all sub-populations and check if the KEY matches
        // (with neuron ID masked out)
        for (int j = 0; j < pre_pop_info->no_pre_vertices; j++) {
            const key_atom_info_t *kai = &pre_pop_info->key_atom_info[j];
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

//! \brief Get the sub-population id and sub-population-based neuron id given
//!        the population id and the population-based neuron id
//! \param[in] pre_pop_info_table: The prepopulation information table
//! \param[in] population_id: The population ID
//! \param[in] pop_neuron_id: The ID of the neuron within the population
//! \param[out] sub_population_id: The ID of the sub-population
//! \param[out] sub_pop_neuron_id:
//!     The ID of the neuron within the sub-population
//! \param[out] spike: The spike associated with communication from that neuron
//! \return True if the information was found.
static inline bool sp_structs_get_sub_pop_info(
        const pre_pop_info_table_t *pre_pop_info_table, uint32_t population_id,
        uint32_t pop_neuron_id, uint32_t *restrict sub_population_id,
        uint32_t *restrict sub_pop_neuron_id, uint32_t *restrict spike) {
    const pre_info_t *app_pop_info =
            pre_pop_info_table->prepop_info[population_id];
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

//! \brief Removes a synapse from the relevant structures
//! \param[in,out] current_state: Describes what is to be done
//! \param[in,out] row: The row of the synaptic matrix to be updated
//! \return True if the synapse was removed
static inline bool sp_structs_remove_synapse(
        current_state_t *restrict current_state, synaptic_row_t restrict row) {
    if (!synapse_dynamics_remove_neuron(current_state->offset, row)) {
        return false;
    }

    current_state->post_to_pre_table_entry->neuron_index = 0xFFFF;
    return true;
}

//! \brief Adds a synapse to the relevant structures
//! \param[in,out] current_state: Describes what is to be done
//! \param[in,out] row: The row of the synaptic matrix to be updated
//! \return True if the synapse was added
static inline bool sp_structs_add_synapse(
        current_state_t *restrict current_state, synaptic_row_t restrict row) {
    uint32_t appr_scaled_weight = current_state->pre_population_info->weight;

    uint32_t actual_delay;
    uint32_t offset = current_state->pre_population_info->delay_hi -
            current_state->pre_population_info->delay_lo;
    actual_delay = rand_int(offset, *(current_state->local_seed)) +
            current_state->pre_population_info->delay_lo;

    if (!synapse_dynamics_add_neuron(
            current_state->post_syn_id, row, appr_scaled_weight, actual_delay,
			current_state->pre_population_info->connection_type)) {
        return false;
    }

    // Critical: tell the compiler that this pointer is aligned so it doesn't
    // internally convert the assignment to a memcpy(), which is a saving of
    // hundreds of bytes...
    post_to_pre_entry *ppentry = __builtin_assume_aligned(
            current_state->post_to_pre_table_entry, 4);
    *ppentry = current_state->post_to_pre;
    return true;
}

//! \brief Common code for structural plasticity initialisation.
//! \param[in] sdram_sp_address: Address of the configuration region.
//! \param[in,out] rewiring_data:
//!     Address of the rewiring information structure to fill out.
//! \param[in,out] pre_info:
//!     The pre-population information structure to fill out.
//! \param[out] post_to_pre_table: Variable to receive the address of the
//!     post-population-to-pre-population mapping table that this function
//!     discovers in the configuration region.
//! \return pointer to the next piece of memory after the common section of the
//!     configuration region.
static inline uint8_t *sp_structs_read_in_common(
        address_t sdram_sp_address, rewiring_data_t *rewiring_data,
        pre_pop_info_table_t *pre_info, post_to_pre_entry **post_to_pre_table) {
    uint8_t *data = (uint8_t *) sdram_sp_address;
    spin1_memcpy(rewiring_data, data, sizeof(rewiring_data_t));
    data += sizeof(rewiring_data_t);

    pre_info->no_pre_pops = rewiring_data->no_pre_pops;
    pre_info->prepop_info = spin1_malloc(
            rewiring_data->no_pre_pops * sizeof(pre_info_t *));
    if (pre_info->prepop_info == NULL) {
        log_error("Could not initialise pre population info");
        rt_error(RTE_SWERR);
    }
    for (uint32_t i = 0; i < rewiring_data->no_pre_pops; i++) {
        pre_info->prepop_info[i] = (pre_info_t *) data;
        uint32_t pre_size = (pre_info->prepop_info[i]->no_pre_vertices
                * sizeof(key_atom_info_t)) + sizeof(pre_info_t);
        pre_info->prepop_info[i] = spin1_malloc(pre_size);
        if (pre_info->prepop_info[i] == NULL) {
            log_error("Could not initialise pre population info %d", i);
            rt_error(RTE_SWERR);
        }
        spin1_memcpy(pre_info->prepop_info[i], data, pre_size);

        log_debug("no_pre = %u, sp_control %u, "
                "delay lo %u, delay hi %u, weight %d",
                pre_info->prepop_info[i]->no_pre_vertices,
                pre_info->prepop_info[i]->sp_control,
                pre_info->prepop_info[i]->delay_lo,
                pre_info->prepop_info[i]->delay_hi,
                pre_info->prepop_info[i]->weight);
        log_debug("connection_type = %d, total_no_atoms=%d",
                pre_info->prepop_info[i]->connection_type,
                pre_info->prepop_info[i]->total_no_atoms);
        data += pre_size;
    }

    *post_to_pre_table = (post_to_pre_entry *) data;
    uint32_t n_elements =
            rewiring_data->s_max * rewiring_data->machine_no_atoms;

    for (uint32_t i=0; i < n_elements; i++){
        log_debug("index %d, pop index %d, sub pop index %d, neuron_index %d",
                i, (*post_to_pre_table)[i].pop_index,
                (*post_to_pre_table)[i].sub_pop_index,
                (*post_to_pre_table)[i].neuron_index);
    }
    data += n_elements * sizeof(post_to_pre_entry);
    return (uint8_t *) data;
}

#endif // _SP_STRUCTS_H_
