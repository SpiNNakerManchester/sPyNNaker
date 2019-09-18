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

/*! \file
 *
 * SUMMARY
 *  \brief This file contains the main functions for probabilistic
 *  synaptogenesis.
 *
 * Author: Petrut Bogdan
 *
 */
#include <neuron/structural_plasticity/synaptogenesis_dynamics.h>
#include <neuron/population_table/population_table.h>

#include <random.h>
#include <spin1_api.h>
#include <debug.h>
#include <stdfix-full-iso.h>

#include <neuron/synapse_row.h>

#include <neuron/synapses.h>

#include <common/maths-util.h>
#include <simulation.h>

// Interface for rules
#include "partner_selection/partner.h"
#include "elimination/elimination.h"
#include "formation/formation.h"

//-----------------------------------------------------------------------------
// Structures and global data                                                 |
//-----------------------------------------------------------------------------

// the instantiation of the previous struct
rewiring_data_t rewiring_data;

// instantiation of the previous struct
current_state_t current_state;

// inverse of synaptic matrix
post_to_pre_entry *post_to_pre_table;

// pre-population information table
pre_pop_info_table_t pre_info;

// The formation parameters per pre-population
struct formation_params **formation_params;

// The elimination parameters per pre-population
struct elimination_params **elimination_params;


//-----------------------------------------------------------------------------
// Initialisation                                                             |
//-----------------------------------------------------------------------------

//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//! parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address Address of the start of the SDRAM region
//! which contains synaptic rewiring params.
//! \return address_t Address after the final word read from SDRAM.
address_t synaptogenesis_dynamics_initialise(address_t sdram_sp_address) {
    log_info("SR init.");

    uint8_t *data = (uint8_t *) sdram_sp_address;
    spin1_memcpy(&rewiring_data, data, sizeof(rewiring_data));
    data += sizeof(rewiring_data);

    pre_info.no_pre_pops = rewiring_data.no_pre_pops;
    pre_info.prepop_info = spin1_malloc(
            rewiring_data.no_pre_pops * sizeof(pre_info_t *));
    if (pre_info.prepop_info == NULL) {
        log_error("Could not initialise pre population info");
        rt_error(RTE_SWERR);
    }
    for (uint32_t i = 0; i < rewiring_data.no_pre_pops; i++) {
        pre_info.prepop_info[i] = (pre_info_t *) data;
        uint32_t pre_size = (pre_info.prepop_info[i]->no_pre_vertices
                * sizeof(key_atom_info_t)) + sizeof(pre_info_t);
        pre_info.prepop_info[i] = spin1_malloc(pre_size);
        if (pre_info.prepop_info[i] == NULL) {
            log_error("Could not initialise pre population info %d", i);
            rt_error(RTE_SWERR);
        }
        spin1_memcpy(pre_info.prepop_info[i], data, pre_size);
        data += pre_size;
    }

    post_to_pre_table = (post_to_pre_entry *) data;
    uint32_t n_elements = rewiring_data.s_max * rewiring_data.machine_no_atoms;
    data = (uint8_t *) &post_to_pre_table[n_elements];

    partner_init(&data);

    formation_params = spin1_malloc(
        rewiring_data.no_pre_pops * sizeof(struct formation_params *));
    if (formation_params == NULL) {
        log_error("Could not initialise formation parameters");
        rt_error(RTE_SWERR);
    }
    for (uint32_t i = 0; i < rewiring_data.no_pre_pops; i++) {
        formation_params[i] = synaptogenesis_formation_init(&data);
    }

    elimination_params = spin1_malloc(
        rewiring_data.no_pre_pops * sizeof(struct elimination_params *));
    if (elimination_params == NULL) {
        log_error("Could not initialise elimination parameters");
        rt_error(RTE_SWERR);
    }
    for (uint32_t i = 0; i < rewiring_data.no_pre_pops; i++) {
        elimination_params[i] = synaptogenesis_elimination_init(&data);
    }

    return (address_t) data;
}

bool synaptogenesis_dynamics_rewire(
        uint32_t time, spike_t *spike, address_t *synaptic_row_address,
        uint32_t *n_bytes) {

    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) *
            rewiring_data.app_no_atoms;

    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
            post_id > rewiring_data.high_atom) {
        return false;
    }
    post_id -= rewiring_data.low_atom;

    // Select an arbitrary synaptic element for the neurons
    uint32_t row_offset = post_id * rewiring_data.s_max;
    uint32_t column_offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
            rewiring_data.s_max;
    uint32_t total_offset = row_offset + column_offset;
    post_to_pre_entry entry = post_to_pre_table[total_offset];
    uint32_t pre_app_pop = 0, pre_sub_pop = 0, neuron_id = 0;
    if (entry.neuron_index == 0xFFFF) {
        if (!potential_presynaptic_partner(time, &pre_app_pop, &pre_sub_pop,
                &neuron_id, spike)) {
            return false;
        }
    } else {
        pre_app_pop = entry.pop_index;
        pre_sub_pop = entry.sub_pop_index;
        neuron_id = entry.neuron_index;
    }
    pre_info_t *prepop_info = pre_info.prepop_info[pre_app_pop];
    key_atom_info_t *key_atom_info = &prepop_info->key_atom_info[pre_sub_pop];
    if (entry.neuron_index != 0xFFFF) {
        *spike = key_atom_info->key | neuron_id;
    }

    if (!population_table_get_first_address(*spike, synaptic_row_address, n_bytes)) {
        log_error("FAIL@key %d", *spike);
        rt_error(RTE_SWERR);
    }

    // Saving current state
    current_state.pre_syn_id = neuron_id;
    current_state.post_syn_id = post_id;
    current_state.element_exists = entry.neuron_index == 0xFFFF;
    current_state.post_to_pre_table_entry = &post_to_pre_table[total_offset];
    current_state.pre_population_info = prepop_info;
    current_state.key_atom_info = key_atom_info;
    current_state.post_to_pre.neuron_index = neuron_id;
    current_state.post_to_pre.pop_index = pre_app_pop;
    current_state.post_to_pre.sub_pop_index = pre_sub_pop;

    current_state.local_seed = &rewiring_data.local_seed;
    current_state.post_low_atom = rewiring_data.low_atom;
    return true;
}

//! \brief This function is a rewiring DMA callback
//! \param[in] dma_id: the ID of the DMA
//! \param[in] dma_tag: the DMA tag, i.e. the tag used for reading row for
//!                     rewiring
//! \return nothing
bool synaptogenesis_row_restructure(uint32_t time, address_t row) {
    // the selected pre- and postsynaptic IDs are in current_state

    // find the offset of the neuron in the current row
    bool search_hit = synapse_dynamics_find_neuron(
            current_state.post_syn_id, row,
            &(current_state.weight), &(current_state.delay),
            &(current_state.offset));

    if (current_state.element_exists && search_hit) {
        return synaptogenesis_elimination_rule(&current_state,
            elimination_params[current_state.post_to_pre.pop_index], time, row);
    } else {
        // Can't form if the row is full
        uint32_t no_elems = synapse_dynamics_n_connections_in_row(
                synapse_row_fixed_region(row));
        if (no_elems >= rewiring_data.s_max) {
            log_debug("row is full");
            return false;
        }
        return synaptogenesis_formation_rule(&current_state,
            formation_params[current_state.post_to_pre.pop_index], time, row);
    }
}

//! retrieve the period of rewiring
//! based on is_fast(), this can either mean how many times rewiring happens
//! in a timestep, or how many timesteps have to pass until rewiring happens.
int32_t synaptogenesis_rewiring_period(void) {
    return rewiring_data.p_rew;
}

//! controls whether rewiring is attempted multiple times per timestep
//! or after a number of timesteps.
bool synaptogenesis_is_fast(void) {
    return rewiring_data.fast == 1;
}

void synaptogenesis_spike_received(uint32_t time, spike_t spike) {
    partner_spike_received(time, spike);
}
