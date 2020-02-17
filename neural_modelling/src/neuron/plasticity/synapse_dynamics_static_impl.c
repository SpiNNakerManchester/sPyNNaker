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
 *  \brief This file contains the main interface for structural plasticity
 * but no actual code. For that, look at topographic_map_impl.c
 *
 *
 * Author: Petrut Bogdan
 *
 */
#include "synapse_dynamics.h"
#include <debug.h>
#include <utils.h>

static uint32_t synapse_type_index_bits;
static uint32_t synapse_index_bits;
static uint32_t synapse_index_mask;
static uint32_t synapse_type_bits;
static uint32_t synapse_type_mask;

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(address);
    use(ring_buffer_to_input_buffer_left_shifts);

    uint32_t n_neurons_power_2 = n_neurons;
    uint32_t log_n_neurons = 1;
    if (n_neurons != 1) {
        if (!is_power_of_2(n_neurons)) {
            n_neurons_power_2 = next_power_of_2(n_neurons);
        }
        log_n_neurons = ilog_2(n_neurons_power_2);
    }
    uint32_t n_synapse_types_power_2 = n_synapse_types;
    synapse_type_bits = 1;
    if (n_synapse_types != 1) {
        if (!is_power_of_2(n_synapse_types)) {
            n_synapse_types_power_2 = next_power_of_2(n_synapse_types);
        }
        synapse_type_bits = ilog_2(n_synapse_types_power_2);
    }
    synapse_type_index_bits = log_n_neurons + synapse_type_bits;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_type_mask = (1 << synapse_type_bits) - 1;
    return address;
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
}

//---------------------------------------
bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffer, uint32_t time) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer);
    use(time);

    log_error("There should be no plastic synapses!");
    return false;
}

//---------------------------------------
input_t synapse_dynamics_get_intrinsic_bias(
        uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
    return REAL_CONST(0.0);
}

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_left_shifts) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer_to_input_left_shifts);
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(void) {
    return 0;
}

uint32_t synapse_dynamics_get_plastic_saturation_count(void) {
    return 0;
}

bool synapse_dynamics_find_neuron(
        uint32_t id, address_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
    address_t fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region);

    // Loop through plastic synapses
    for (; fixed_synapse > 0; fixed_synapse--) {

        // Get next control word (auto incrementing)
        // Check if index is the one I'm looking for
        uint32_t synaptic_word = *synaptic_words++;
        if (synapse_row_sparse_index(synaptic_word, synapse_index_mask) == id) {
            *offset = synapse_row_num_fixed_synapses(fixed_region) -
                    fixed_synapse;
            *weight = synapse_row_sparse_weight(synaptic_word);
            *delay = synapse_row_sparse_delay(synaptic_word, synapse_type_index_bits);
            *synapse_type = synapse_row_sparse_type(
                    synaptic_word, synapse_index_bits, synapse_type_mask);
            return true;
        }
    }

    return false;
}

bool synapse_dynamics_remove_neuron(uint32_t offset, address_t row) {
    address_t fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region);

   // Delete control word at offset (contains weight)
    synaptic_words[offset] = synaptic_words[fixed_synapse-1];

    // Decrement FF
    fixed_region[0] = fixed_region[0] - 1;
    return true;
}

//! packing all of the information into the required static control word
static inline uint32_t _fixed_synapse_convert(
        uint32_t id, weight_t weight, uint32_t delay, uint32_t type) {
    uint32_t new_synapse = weight << (32 - SYNAPSE_WEIGHT_BITS);
    new_synapse |= ((delay & ((1 << SYNAPSE_DELAY_BITS) - 1)) <<
            synapse_type_index_bits);
    new_synapse |= ((type & ((1 << synapse_type_bits) - 1)) <<
            synapse_index_bits);
    new_synapse |= (id & ((1 << synapse_type_index_bits) - 1));
    return new_synapse;
}

bool synapse_dynamics_add_neuron(
        uint32_t id, address_t row, weight_t weight,
        uint32_t delay, uint32_t type) {
    address_t fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region);
    uint32_t new_synapse = _fixed_synapse_convert(id, weight, delay, type);

    // Add control word at offset
    synaptic_words[fixed_synapse] = new_synapse;

   // Increment FF
    fixed_region[0] = fixed_region[0] + 1;
    return true;
}

uint32_t synapse_dynamics_n_connections_in_row(address_t fixed) {
    return synapse_row_num_fixed_synapses(fixed);
}
