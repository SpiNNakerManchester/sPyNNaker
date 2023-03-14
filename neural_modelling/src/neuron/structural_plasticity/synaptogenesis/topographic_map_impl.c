/*
 * Copyright (c) 2016 The University of Manchester
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

/*! \file
 * \brief This file contains the main functions for probabilistic
 * synaptogenesis.
 *
 * \author Petrut Bogdan
 */
#include <neuron/structural_plasticity/synaptogenesis_dynamics.h>
#include <neuron/population_table/population_table.h>

#include <random.h>
#include <spin1_api.h>
#include <debug.h>
#include <stdfix-full-iso.h>
#include <circular_buffer.h>
#include <recording.h>

#include <neuron/synapse_row.h>

#include <neuron/synapses.h>

#include <common/maths-util.h>
#include <simulation.h>

// Interface for rules
#include "partner_selection/partner.h"
#include "elimination/elimination.h"
#include "formation/formation.h"

//! values used in recording
enum {
    //! Elimination flag
    ELIM_FLAG = 0,
    //! Formation flag
    FORM_FLAG = 1
};
//! How much to shift post-IDs by
#define ID_SHIFT 1
//! How much to shift pre-IDs by
#define PRE_ID_SHIFT 9

//-----------------------------------------------------------------------------
// Structures and global data                                                 |
//-----------------------------------------------------------------------------

//! the instantiation of the rewiring data
rewiring_data_t rewiring_data;

//! inverse of synaptic matrix
static post_to_pre_entry *post_to_pre_table;

//! pre-population information table
pre_pop_info_table_t pre_info;

//! The formation parameters per pre-population
static formation_params_t **formation_params;

//! The elimination parameters per pre-population
static elimination_params_t **elimination_params;

//! \brief Current states in use.
//!
//! synaptogenesis_row_restructure() moves states from here to ::free_states
static circular_buffer current_state_queue;

//! \brief Free current states.
//!
//! synaptogenesis_dynamics_rewire() moves states from here to
//! ::current_state_queue
static circular_buffer free_states;

//! The recording region for the structural events
uint32_t rewiring_recording_index;

//! Struct for structural recording data
typedef struct structural_recording_values_t {
    uint32_t time;
    uint32_t value;
} structural_recording_values_t;

//! Working buffer for the recording of structural changes
structural_recording_values_t structural_recording_values;

//! Timer callbacks since last rewiring
static uint32_t last_rewiring_time = 0;

void print_post_to_pre_entry(void) {
    uint32_t n_elements =
            rewiring_data.s_max * rewiring_data.machine_no_atoms;

    for (uint32_t i=0; i < n_elements; i++) {
        log_debug("index %d, pop index %d, sub pop index %d, neuron_index %d",
                i, post_to_pre_table[i].pop_index,
                post_to_pre_table[i].sub_pop_index,
                post_to_pre_table[i].neuron_index);
    }
}

//-----------------------------------------------------------------------------
// Access helpers for circular buffers
//-----------------------------------------------------------------------------
static inline void _queue_state(current_state_t *state) {
    if (__builtin_expect(
            !circular_buffer_add(current_state_queue, (uint32_t) state), 0)) {
        log_error("Could not add state (0x%08x) to queued states", state);
        rt_error(RTE_SWERR);
    }
}

static inline current_state_t *_get_state(void) {
    current_state_t *state;
    if (__builtin_expect(
            !circular_buffer_get_next(current_state_queue, (uint32_t *) &state),
            0)) {
        log_error("Could not read a state!");
        rt_error(RTE_SWERR);
    }
    return state;
}

static inline void _free_state(current_state_t *state) {
    if (__builtin_expect(
            !circular_buffer_add(free_states, (uint32_t) state), 0)) {
        log_error("Could not add state (0x%08x) to free states", state);
        rt_error(RTE_SWERR);
    }
}

static inline current_state_t *_alloc_state(void) {
    current_state_t *state;
    if (__builtin_expect(
            !circular_buffer_get_next(free_states, (uint32_t *) &state), 0)) {
        log_error("Ran out of states!");
        rt_error(RTE_SWERR);
    }
    return state;
}

//-----------------------------------------------------------------------------
// Initialisation                                                             |
//-----------------------------------------------------------------------------

bool synaptogenesis_dynamics_initialise(
        address_t sdram_sp_address, uint32_t *recording_regions_used) {
    uint8_t *data = sp_structs_read_in_common(
            sdram_sp_address, &rewiring_data, &pre_info, &post_to_pre_table);

    // Allocate current states
    uint32_t n_states = 1;
    if (rewiring_data.fast) {
        n_states = rewiring_data.p_rew;
    }
    log_debug("Rewiring period %u, fast=%u, n_states=%u",
            rewiring_data.p_rew, rewiring_data.fast, n_states);
    // Add one to number of states as buffer wastes an entry
    current_state_queue = circular_buffer_initialize(n_states + 1);
    if (current_state_queue == NULL) {
        log_error("Could not allocate current state queue");
        rt_error(RTE_SWERR);
    }
    // Add one to number of states as buffer wastes an entry
    free_states = circular_buffer_initialize(n_states + 1);
    if (free_states == NULL) {
        log_error("Could not allocate free state queue");
    }
    current_state_t *states = spin1_malloc(n_states * sizeof(current_state_t));
    if (states == NULL) {
        log_error("Could not allocate states");
        rt_error(RTE_SWERR);
    }
    for (uint32_t i = 0; i < n_states; i++) {
        _free_state(&states[i]);
    }

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

    rewiring_recording_index = *recording_regions_used;
    *recording_regions_used = rewiring_recording_index + 1;

    log_debug("The rewiring_recording_index is %u", rewiring_recording_index);

    return true;
}

bool synaptogenesis_dynamics_rewire(
        uint32_t time, spike_t *spike, pop_table_lookup_result_t *result) {

    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id = rand_int(rewiring_data.app_no_atoms,
        rewiring_data.shared_seed);

    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
            post_id > rewiring_data.high_atom) {
        return false;
    }
    post_id -= rewiring_data.low_atom;

    // Select an arbitrary synaptic element for the neurons
    uint32_t row_offset = post_id * rewiring_data.s_max;
    uint32_t column_offset = rand_int(rewiring_data.s_max,
            rewiring_data.local_seed);
    uint32_t total_offset = row_offset + column_offset;
    post_to_pre_entry entry = post_to_pre_table[total_offset];
    uint32_t pre_app_pop = 0, pre_sub_pop = 0, m_pop_index = 0, neuron_id = 0;
    if (entry.neuron_index == 0xFFFF) {
        if (!potential_presynaptic_partner(time, &pre_app_pop, &pre_sub_pop,
                &neuron_id, spike, &m_pop_index)) {
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
        *spike = key_atom_info->key | (neuron_id << key_atom_info->n_colour_bits);
        m_pop_index = key_atom_info->m_pop_index;
    }

    if (!population_table_get_first_address(*spike, result)) {
        log_error("FAIL@key %d", *spike);
        rt_error(RTE_SWERR);
    }
    uint32_t index = 0;
    while (index < m_pop_index) {
        if (!population_table_get_next_address(spike, result)) {
            log_error("FAIL@key %d, index %d (failed at %d)",
                    *spike, m_pop_index, index);
            rt_error(RTE_SWERR);
        }
        index++;
    }

    // Saving current state
    current_state_t *current_state = _alloc_state();
    current_state->pre_syn_id = neuron_id;
    current_state->post_syn_id = post_id;
    current_state->element_exists = entry.neuron_index != 0xFFFF;
    current_state->post_to_pre_table_entry = &post_to_pre_table[total_offset];
    current_state->pre_population_info = prepop_info;
    current_state->key_atom_info = key_atom_info;
    current_state->post_to_pre.neuron_index = neuron_id;
    current_state->post_to_pre.pop_index = pre_app_pop;
    current_state->post_to_pre.sub_pop_index = pre_sub_pop;
    current_state->local_seed = &rewiring_data.local_seed;
    current_state->post_low_atom = rewiring_data.low_atom;
    current_state->with_replacement = rewiring_data.with_replacement;
    _queue_state(current_state);
    return true;
}

static bool do_formation(uint32_t time, synaptic_row_t restrict row,
        current_state_t *restrict current_state) {
	if (synaptogenesis_formation_rule(current_state,
			formation_params[current_state->post_to_pre.pop_index], time, row)) {
		// Create recorded value
		// (bottom bit: add/remove, next 8: local id, remainder: pre global id)
		uint32_t pre_id = current_state->key_atom_info->lo_atom
				+ current_state->pre_syn_id;
		uint32_t id = current_state->post_syn_id;
		uint32_t record_value = FORM_FLAG | (id << ID_SHIFT) |
				(pre_id << PRE_ID_SHIFT);
		structural_recording_values.time = time;
		structural_recording_values.value = record_value;
		recording_record(rewiring_recording_index, &structural_recording_values,
				sizeof(structural_recording_values_t));

		return true;
	}
	return false;
}

//! \brief Performs the actual restructuring of a row
//! \details Supporting function for synaptogenesis_row_restructure()
//! \param[in] time: The time of the restructure
//! \param[in] row: The row to restructure
//! \param[in] current_state: The current state of the world
//! \return True if the row was changed and needs to be written back
static inline bool row_restructure(
        uint32_t time, synaptic_row_t restrict row,
        current_state_t *restrict current_state) {
    // the selected pre- and postsynaptic IDs are in current_state

    if (current_state->element_exists) {
        // find the offset of the neuron in the current row
        if (!synapse_dynamics_find_neuron(
                current_state->post_syn_id, row,
                &current_state->weight, &current_state->delay,
                &current_state->offset, &current_state->synapse_type)) {
            log_debug("Post neuron %u not in row", current_state->post_syn_id);
            return false;
        }

        if (synaptogenesis_elimination_rule(current_state,
                elimination_params[current_state->post_to_pre.pop_index],
                time, row)) {
            // Create recorded value
            // (bottom bit: add/remove, next 8: local id, remainder: pre global id)
            uint32_t pre_id = current_state->key_atom_info->lo_atom + current_state->pre_syn_id;
            uint32_t id = current_state->post_syn_id;
            uint32_t record_value = ELIM_FLAG | (id << ID_SHIFT) | (pre_id << PRE_ID_SHIFT);
            structural_recording_values.time = time;
            structural_recording_values.value = record_value;
            recording_record(rewiring_recording_index, &structural_recording_values,
                    sizeof(structural_recording_values_t));

            return true;
        } else {
            return false;
        }

    } else {
        // Can't form if the row is full
        uint32_t no_elems = synapse_dynamics_n_connections_in_row(
                synapse_row_fixed_region(row));
        if (no_elems >= rewiring_data.s_max) {
            return false;
        } else {
            if (current_state->with_replacement) {
                // A synapse can be added anywhere on the current row, so just do it
            	return do_formation(time, row, current_state);
            } else {
                // A synapse cannot be added if one exists between the current pair of neurons
                if (!synapse_dynamics_find_neuron(
                      current_state->post_syn_id, row,
                      &(current_state->weight), &(current_state->delay),
                      &(current_state->offset), &(current_state->synapse_type))) {
                    return do_formation(time, row, current_state);
        		} else {
        		    log_debug("Post neuron %u already in row", current_state->post_syn_id);
        		    return false;
        		}
            }
        }
    }
}

bool synaptogenesis_row_restructure(uint32_t time, synaptic_row_t row) {
    current_state_t *current_state = _get_state();
    bool return_value = row_restructure(time, row, current_state);
    _free_state(current_state);
    return return_value;
}

void synaptogenesis_spike_received(uint32_t time, spike_t spike) {
    partner_spike_received(time, spike);
}

uint32_t synaptogenesis_n_updates(void) {
    if (rewiring_data.fast) {
        return rewiring_data.p_rew;
    }

    last_rewiring_time++;
    if (last_rewiring_time >= rewiring_data.p_rew) {
        last_rewiring_time = 0;
        return 1;
    }

    return 0;
}
