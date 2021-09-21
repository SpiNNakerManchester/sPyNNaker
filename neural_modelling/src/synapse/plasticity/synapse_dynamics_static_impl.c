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

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts, bool *has_plastic_synapses) {
    use(address);
    use(n_neurons);
    use(n_synapse_types);
    use(ring_buffer_to_input_buffer_left_shifts);

    *has_plastic_synapses = false;
    
    return address;
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    use(neuron_index);
    use(time);
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

//! \brief  Don't search the synaptic row for the the connection with the
//!         specified post-synaptic ID -- no rewiring here
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_plastic_neuron_with_id(
        uint32_t id, address_t row, structural_plasticity_data_t *sp_data) {
    use(id);
    use(row);
    use(sp_data);
    return false;
}

//! \brief  Don't remove the entry at the specified offset in the synaptic row
//! -- no rewiring here
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row) {
    use(offset);
    use(row);
    return false;
}

//! \brief  Don't add a plastic entry in the synaptic row -- no rewiring here
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_plastic_neuron_with_id(
        uint32_t id, address_t row, uint32_t weight, uint32_t delay, uint32_t type) {
    use(id);
    use(row);
    use(weight);
    use(delay);
    use(type);
    return false;
}

void synapse_dynamics_set_post_buffer_region(uint32_t tag) {
    use(tag);
}

void synapse_dynamics_read_post_buffer() {

}
