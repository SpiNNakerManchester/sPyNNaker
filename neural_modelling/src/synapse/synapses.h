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

#ifndef _SYNAPSES_H_
#define _SYNAPSES_H_

#include <common/neuron-typedefs.h>
#include <synapse/structural_plasticity/sp_structs.h>
#include "synapse_row.h"
#include "neuron/neuron.h"

// Get the index of the ring buffer for a given timestep, synapse type and
// neuron index
static inline index_t synapses_get_ring_buffer_index(
        uint32_t simuation_timestep, uint32_t synapse_type_index,
        uint32_t neuron_index, uint32_t synapse_type_index_bits,
        uint32_t synapse_index_bits) {
    return (((simuation_timestep & SYNAPSE_DELAY_MASK)
             << synapse_type_index_bits)
            | (synapse_type_index << synapse_index_bits)
            | neuron_index);
}

// Get the index of the ring buffer for a given timestep and combined
// synapse type and neuron index (as stored in a synapse row)
static inline index_t synapses_get_ring_buffer_index_combined(
        uint32_t simulation_timestep,
        uint32_t combined_synapse_neuron_index,
        uint32_t synapse_type_index_bits) {
    return (((simulation_timestep & SYNAPSE_DELAY_MASK)
             << synapse_type_index_bits)
            | combined_synapse_neuron_index);
}

// Converts a weight stored in a synapse row to an input
static inline input_t synapses_convert_weight_to_input(
        int32_t weight, uint32_t left_shift) {
    union {
        int_k_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (int_k_t) (weight) << left_shift;

    return converter.output_type;
}

static inline void synapses_print_weight(
        weight_t weight, uint32_t left_shift) {
    if (weight != 0) {
        io_printf(IO_BUF, "%12.6k",
                synapses_convert_weight_to_input(weight, left_shift));
    } else {
        io_printf(IO_BUF, "      ");
    }
}

bool synapses_initialise(
        address_t address, address_t direct_matrix_address,
        uint32_t *n_neurons_value, uint32_t *n_synapse_types_value,
        uint32_t *incoming_rate_buffer_size,
        uint32_t **ring_buffer_to_input_buffer_left_shifts,
        address_t *direct_synapses_address,
        uint32_t *writing_time);

void synapses_do_timestep_update(timer_t time);

//! \brief process a synaptic row
//! \param[in] time: the simulated time
//! \param[in] row: the synaptic row in question
//! \param[in] write: bool saying if to write this back to SDRAM
//! \param[in] process_id: ??????????????????
//! \param[in] rate: input rate
//! \return bool if successful or not
bool synapses_process_synaptic_row(
        uint32_t time, synaptic_row_t row, bool write, uint32_t process_id);

//! \brief returns the number of times the synapses have saturated their
//!        weights.
//! \return the number of times the synapses have saturated.
uint32_t synapses_get_saturation_count(void);

//! \brief returns the counters for plastic and fixed pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t synapses_get_pre_synaptic_events(void);


//------------------------------------------------------------------------------
// Synaptic rewiring functions
//------------------------------------------------------------------------------

//! \brief  Searches the synaptic row for the the connection with the
//!         specified post-synaptic ID
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_static_neuron_with_id(
        uint32_t id, address_t row, structural_plasticity_data_t *sp_data);

//! \brief  Remove the entry at the specified offset in the synaptic row
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_static_neuron_at_offset(uint32_t offset, address_t row);

//! \brief  Add a static entry in the synaptic row
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_static_neuron_with_id(
        uint32_t id, address_t row, uint32_t weight, uint32_t delay,
        uint32_t type);

void synapses_set_contribution_region();

void synapses_process_post_synaptic_event(uint32_t time);

void synapses_flush_ring_buffer(uint32_t timestep);

// DEFINED IN NEURON.H
//! \brief This function adds two s1615 values, saturating the result.
//!        It uses the ARM assembly instruction QADD for efficiency.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return x+y.
//
// static inline s1615 sat_accum_sum(
// 	s1615 x,
// 	s1615 y)
// {
//     register s1615 r;

//     asm volatile("qadd %[r], %[x], %[y]"
// 	    : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );
//     return r;
// }

#endif // _SYNAPSES_H_
