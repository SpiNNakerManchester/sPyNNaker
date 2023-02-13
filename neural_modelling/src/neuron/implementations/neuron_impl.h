/*
 * Copyright (c) 2017-2023 The University of Manchester
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

//! \dir
//! \brief Neuron implementations
//! \file
//! \brief General API of a neuron implementation
#ifndef _NEURON_IMPL_H_
#define _NEURON_IMPL_H_

#include <common/neuron-typedefs.h>
#include <neuron/send_spike.h>

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons: The number of neurons
//! \return True if successful
static bool neuron_impl_initialise(uint32_t n_neurons);

//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index: the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index: the index of the neuron
//! \param[in] weights_this_timestep: weight inputs to be added
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep);

//! \brief Load in the neuron parameters
//! \param[in] address: SDRAM block to read parameters from
//! \param[in] next: Offset of next address in store
//! \param[in] n_neurons: The number of neurons
//! \param[in] save_initial_state: If not 0, the address to copy the state to
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons,
		address_t save_initial_state);

//! \brief Do the timestep update for the particular implementation
//! \param[in] timer_count: The timer count, used for TDMA packet spreading
//! \param[in] time: The time step of the update
//! \param[in] n_neurons: The number of neurons
static void neuron_impl_do_timestep_update(
        uint32_t timer_count, uint32_t time, uint32_t n_neurons);

//! \brief Stores neuron parameters back into SDRAM
//! \param[out] address: the address in SDRAM to start the store
//! \param[in] next: Offset of next address in store
//! \param[in] n_neurons: The number of neurons
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons);

#if LOG_LEVEL >= LOG_DEBUG
//! \brief Print the inputs to the neurons
//! \param[in] n_neurons: The number of neurons
static void neuron_impl_print_inputs(uint32_t n_neurons);

//! \brief Print the synapse parameters of the neurons
//! \param[in] n_neurons: The number of neurons
static void neuron_impl_print_synapse_parameters(uint32_t n_neurons);

//! \brief Get the synapse type character for a synapse type
//! \param[in] synapse_type: The synapse type
//! \return The descriptor character (sometimes two characters)
static const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type);
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_H_
