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
//! \brief Operations on synapses
#ifndef _SYNAPSES_H_
#define _SYNAPSES_H_

#include <common/neuron-typedefs.h>
#include "synapse_row.h"
#include "meanfield.h"

//! Count of the number of times the synapses have saturated their weights.
extern uint32_t synapses_saturation_count;


//! \brief Get the index of the ring buffer for a given timestep, synapse type
//!     and neuron index
//! \param[in] simulation_timestep:
//! \param[in] synapse_type_index:
//! \param[in] neuron_index:
//! \param[in] synapse_type_index_bits:
//! \param[in] synapse_index_bits:
//! \return Index into the ring buffer
static inline index_t synapses_get_ring_buffer_index(
        uint32_t simulation_timestep, uint32_t synapse_type_index,
        uint32_t neuron_index, uint32_t synapse_type_index_bits,
        uint32_t synapse_index_bits) {
    return ((simulation_timestep & SYNAPSE_DELAY_MASK) << synapse_type_index_bits)
            | (synapse_type_index << synapse_index_bits)
            | neuron_index;
}

//! \brief Get the index of the ring buffer for a given timestep and combined
//!     synapse type and neuron index (as stored in a synapse row)
//! \param[in] simulation_timestep:
//! \param[in] combined_synapse_neuron_index:
//! \param[in] synapse_type_index_bits:
//! \return Index into the ring buffer
static inline index_t synapses_get_ring_buffer_index_combined(
        uint32_t simulation_timestep,
        uint32_t combined_synapse_neuron_index,
        uint32_t synapse_type_index_bits) {
    return ((simulation_timestep & SYNAPSE_DELAY_MASK) << synapse_type_index_bits)
            | combined_synapse_neuron_index;
}

//! \brief Converts a weight stored in a synapse row to an input
//! \param[in] weight: the weight to convert in synapse-row form
//! \param[in] left_shift: the shift to use when decoding
//! \return the actual input weight for the model
static inline input_t synapses_convert_weight_to_input(
        weight_t weight, uint32_t left_shift) {
    union {
        int_k_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (int_k_t) (weight) << left_shift;

    return converter.output_type;
}

//! \brief Print the weight of a synapse
//! \param[in] weight: the weight to print in synapse-row form
//! \param[in] left_shift: the shift to use when decoding
static inline void synapses_print_weight(
        weight_t weight, uint32_t left_shift) {
    if (weight != 0) {
        io_printf(IO_BUF, "%12.6k",
                synapses_convert_weight_to_input(weight, left_shift));
    } else {
        io_printf(IO_BUF, "      ");
    }
}

//! \brief Initialise the synapse processing
//! \param[in] synapse_params_address: Synapse configuration in SDRAM
//! \param[in] n_neurons: Number of neurons to simulate
//! \param[in] n_synapse_types: Number of synapse types
//! \param[out] ring_buffer_to_input_buffer_left_shifts:
//!     Array of shifts to use when converting from ring buffer values to input
//!     buffer values
//! \return True if successfully initialised. False otherwise.
bool synapses_initialise(
        address_t synapse_params_address,
        uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t **ring_buffer_to_input_buffer_left_shifts,
        bool* clear_input_buffers_of_late_packets_init);

//! \brief Do all the synapse processing for a timestep.
//! \param[in] time: the current simulation time
void synapses_do_timestep_update(timer_t time);

//! \brief process a synaptic row
//! \param[in] time: the simulated time
//! \param[in] row: the synaptic row in question
//! \param[out] write_back: whether to write back to SDRAM
//! \return True if successful
bool synapses_process_synaptic_row(
        uint32_t time, synaptic_row_t row, bool *write_back);

//! \brief returns the counters for plastic and fixed pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t synapses_get_pre_synaptic_events(void);

//! \brief flush the ring buffers
void synapses_flush_ring_buffers(void);

//! \brief allows clearing of DTCM used by synapses
//! \return true if successful, false otherwise
bool synapses_shut_down(void);

#endif // _SYNAPSES_H_
