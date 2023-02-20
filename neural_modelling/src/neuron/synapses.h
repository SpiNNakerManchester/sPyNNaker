/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
//! \param[in] min_weight: the minimum weight to use in the conversion
static inline void synapses_print_weight(
        weight_t weight, REAL min_weight) {
    if (weight != 0) {
        io_printf(IO_BUF, "%12.6k",
                synapse_row_convert_weight_to_input(weight, min_weight));
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
        weight_t **ring_buffers, REAL **min_weights,
        bool* clear_input_buffers_of_late_packets_init,
        uint32_t *incoming_spike_buffer_size);

//! \brief process a synaptic row
//! \param[in] time: the simulated time
//! \param[in] spike_colour: the colour extracted from the spike key
//! \param[in] colour_mask: the colour mask extracted from the pop table
//! \param[in] row: the synaptic row in question
//! \param[out] write_back: whether to write back to SDRAM
//! \return True if successful
bool synapses_process_synaptic_row(
        uint32_t time, uint32_t spike_colour, uint32_t colour_mask,
		synaptic_row_t row, bool *write_back);

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
