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

#ifndef _NEURON_IMPL_H_
#define _NEURON_IMPL_H_

#include <common/neuron-typedefs.h>

//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons The number of neurons
//! \return bool
static bool neuron_impl_initialise(uint32_t n_neurons);

//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index the index of the neuron
//! \param[in] weights_this_timestep weight inputs to be added
//! \return None
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep);

//! \brief Load in the neuron parameters
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons);

//! \brief Do the timestep update for the particular implementation
//! \param[in] neuron_index The index of the neuron to update
//! \param[in] external_bias External input to be applied to the neuron
//! \return bool value for whether a spike has occurred
static bool neuron_impl_do_timestep_update(
        index_t neuron_index, input_t external_bias);

//! \brief Store the neuron parameters to the given address
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons);

#if LOG_LEVEL >= LOG_DEBUG
void neuron_impl_print_inputs(uint32_t n_neurons);

void neuron_impl_print_synapse_parameters(uint32_t n_neurons);

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type);
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_H_
