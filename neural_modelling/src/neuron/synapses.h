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
#include <debug.h>
#include "synapse_row.h"

//! \brief Number of bits needed for the synapse type and index
//! \details
//! ```
//! synapse_index_bits + synapse_type_bits
//! ```
extern uint32_t synapse_type_index_bits;
//! \brief Mask to pick out the synapse type and index.
//! \details
//! ```
//! synapse_index_mask | synapse_type_mask
//! ```
extern uint32_t synapse_type_index_mask;
//! Number of bits in the synapse index
extern uint32_t synapse_index_bits;
//! Mask to pick out the synapse index.
extern uint32_t synapse_index_mask;
//! Number of bits in the synapse type
extern uint32_t synapse_type_bits;
//! Mask to pick out the synapse type.
extern uint32_t synapse_type_mask;
//! Number of bits in the delay
extern uint32_t synapse_delay_bits;
//! Mask to pick out the delay
extern uint32_t synapse_delay_mask;

//! Count of the number of times the synapses have saturated their weights.
extern uint32_t synapses_saturation_count;

//! Count of the synapses that have been skipped because the delay wasn't
//! big enough given how long the spike took to arrive
extern uint32_t skipped_synapses;

//! Count of the spikes that are received late
extern uint32_t late_spikes;

//! The maximum lateness of a spike
extern uint32_t max_late_spike;


//! \brief Print the weight of a synapse
//! \param[in] weight: the weight to print in synapse-row form
//! \param[in] left_shift: the shift to use when decoding
static inline void synapses_print_weight(
        weight_t weight, uint32_t left_shift) {
    if (weight != 0) {
        io_printf(IO_BUF, "%12.6k",
                synapse_row_convert_weight_to_input(weight, left_shift));
    } else {
        io_printf(IO_BUF, "      ");
    }
}

//! \brief Initialise the synapse processing
//! \param[in] synapse_params_address: Synapse configuration in SDRAM
//! \param[out] n_neurons: Number of neurons that will be simulated
//! \param[out] n_synapse_types: Number of synapse types that will be simulated
//! \param[out] ring_buffers: The ring buffers that will be used
//! \param[out] ring_buffer_to_input_buffer_left_shifts:
//!     Array of shifts to use when converting from ring buffer values to input
//!     buffer values
//! \param[out] clear_input_buffers_of_late_packets_init:
//!     Inicates whether to clear the input buffers each time step
//! \param[out] incoming_spike_buffer_size:
//!     The number of spikes to support in the incoming spike circular buffer
//! \return True if successfully initialised. False otherwise.
bool synapses_initialise(
        address_t synapse_params_address,
        uint32_t *n_neurons, uint32_t *n_synapse_types,
        weight_t **ring_buffers,
        uint32_t **ring_buffer_to_input_buffer_left_shifts,
        bool* clear_input_buffers_of_late_packets_init,
        uint32_t *incoming_spike_buffer_size);

//! \brief process a synaptic row
//! \param[in] time: the simulated time
//! \param[in] row: the synaptic row in question
//! \param[out] write_back: whether to write back to SDRAM
//! \return True if successful
bool synapses_process_synaptic_row(
        uint32_t time, uint32_t spike_colour, synaptic_row_t row, bool *write_back);

//! \brief returns the counters for plastic and fixed pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t synapses_get_pre_synaptic_events(void);

//! \brief Resume processing of synapses after a pause
//! \param[in] time: The time at which the simulation is to start
void synapses_resume(timer_t time);

//! \brief Reset the ring buffers to 0 at the given time
//! \param[in] time: the simulated time to reset the buffers at
void synapses_flush_ring_buffers(timer_t time);

#endif // _SYNAPSES_H_
