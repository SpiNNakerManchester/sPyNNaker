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

/*!
 * \file
 * \brief This file contains the main interface for structural plasticity
 * and some shared code. For the main implementation, see topographic_map_impl.c
 *
 * \author Petrut Bogdan
 */
#include "synapse_dynamics.h"
#include <neuron/synapses.h>
#include <debug.h>
#include <utils.h>

bool synapse_dynamics_initialise(
        UNUSED address_t address, UNUSED uint32_t n_neurons,
        UNUSED uint32_t n_synapse_types,
        UNUSED REAL *min_weights) {
    return true;
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        UNUSED uint32_t time, UNUSED index_t neuron_index) {
}

//---------------------------------------
bool synapse_dynamics_process_plastic_synapses(
        UNUSED synapse_row_plastic_data_t *plastic_region_data,
        UNUSED synapse_row_fixed_part_t *fixed_region,
        UNUSED weight_t *ring_buffer, UNUSED uint32_t time) {
    log_error("There should be no plastic synapses!");
    return false;
}

void synapse_dynamics_print_plastic_synapses(
        UNUSED synapse_row_plastic_data_t *plastic_region_data,
        UNUSED synapse_row_fixed_part_t *fixed_region,
        UNUSED REAL *min_weights) {
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(void) {
    return 0;
}

uint32_t synapse_dynamics_get_plastic_saturation_count(void) {
    return 0;
}

bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(fixed_region);

    // Loop through plastic synapses
    for (; fixed_synapse > 0; fixed_synapse--) {

        // Get next control word (auto incrementing)
        // Check if index is the one I'm looking for
        uint32_t synaptic_word = *synaptic_words++;
        if (synapse_row_sparse_index(synaptic_word, synapse_index_mask) == id) {
            *offset = synapse_row_num_fixed_synapses(fixed_region) -
                    fixed_synapse;
            *weight = synapse_row_sparse_weight(synaptic_word);
            *delay = synapse_row_sparse_delay(synaptic_word,
                    synapse_type_index_bits, synapse_delay_mask);
            *synapse_type = synapse_row_sparse_type(
                    synaptic_word, synapse_index_bits, synapse_type_mask);
            return true;
        }
    }

    return false;
}

bool synapse_dynamics_remove_neuron(uint32_t offset, synaptic_row_t row) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(fixed_region);

    // Delete control word at offset (contains weight)
    synaptic_words[offset] = synaptic_words[fixed_synapse - 1];

    // Decrement FF
    fixed_region->num_fixed--;
    return true;
}

//! packing all of the information into the required static control word
static inline uint32_t _fixed_synapse_convert(
        uint32_t id, weight_t weight, uint32_t delay, uint32_t type) {
    uint32_t new_synapse = weight << (32 - SYNAPSE_WEIGHT_BITS);
    new_synapse |= ((delay & ((1 << synapse_delay_bits) - 1)) <<
            synapse_type_index_bits);
    new_synapse |= ((type & ((1 << synapse_type_bits) - 1)) <<
            synapse_index_bits);
    new_synapse |= (id & ((1 << synapse_type_index_bits) - 1));
    return new_synapse;
}

bool synapse_dynamics_add_neuron(
        uint32_t id, synaptic_row_t row, weight_t weight,
        uint32_t delay, uint32_t type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(fixed_region);
    uint32_t new_synapse = _fixed_synapse_convert(id, weight, delay, type);

    // Add control word at offset
    synaptic_words[fixed_synapse] = new_synapse;

    // Increment FF
    fixed_region->num_fixed++;
    return true;
}

uint32_t synapse_dynamics_n_connections_in_row(
        synapse_row_fixed_part_t *fixed) {
    return synapse_row_num_fixed_synapses(fixed);
}
