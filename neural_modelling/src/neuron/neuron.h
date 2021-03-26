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
 *  \brief interface for neurons
 *
 *  The API contains:
 *    - neuron_initialise(address, recording_flags, n_neurons_value):
 *         translate the data stored in the NEURON_PARAMS data region in SDRAM
 *         and converts it into c based objects for use.
 *    - neuron_set_input_buffers(input_buffers_value):
 *         setter for the internal input buffers
 *    - neuron_do_timestep_update(time):
 *         executes all the updates to neural parameters when a given timer
 *         period has occurred.
 */

#ifndef _NEURON_H_
#define _NEURON_H_

#include <common/neuron-typedefs.h>
#include "recording.h"

//! \brief translate the data stored in the NEURON_PARAMS data region in SDRAM
//!        and convert it into c based objects for use.
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[out] n_neurons_value Returns the number of neurons this model is to
//              simulate
//! \param[out] n_synapse_types_value Returns the number of synapse types in
//              the model
//! \param[out] incoming_spike_buffer_size Returns the number of spikes to
//!             support in the incoming spike buffer
//! \param[out] starting_rate Returns the starting rate to set the ring buffer value on synapse side
//! \return boolean which is True is the translation was successful
//!         otherwise False
bool neuron_initialise(
        address_t address, uint32_t *timer_offset);

//! \brief executes all the updates to neural parameters when a given timer
//!        period has occurred.
//! \param[in] time the timer tick value currently being executed
//! \return nothing
void neuron_do_timestep_update(
        uint32_t time, uint timer_count, uint timer_period);

//! \brief interface for reloading neuron parameters as needed
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the reload of the neuron parameters was
//! successful or not
bool neuron_reload_neuron_parameters(address_t address);

//! \brief interface for rewriting the neuron parameters back into SDRAM
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
void neuron_store_neuron_parameters(address_t address);

//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index the index of the neuron
//! \param[in] weights_this_timestep weight inputs to be added
//! \return None
void neuron_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep);

//! \brief This function adds two s1615 values, saturating the result.
//!        It uses the ARM assembly instruction QADD for efficiency.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return x+y.

static inline s1615 sat_accum_sum(
	s1615 x,
	s1615 y)
{
    register s1615 r;

    asm volatile("qadd %[r], %[x], %[y]"
	    : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );
    return r;
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_print_inputs(void);

void neuron_print_synapse_parameters(void);

const char *neuron_get_synapse_type_char(uint32_t synapse_type);
#endif

#endif // _NEURON_H_
