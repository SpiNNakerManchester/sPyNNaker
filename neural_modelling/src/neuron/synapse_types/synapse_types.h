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
//! \brief Synaptic behaviour types
//! \file
//! \brief API for synaptic behaviour types
//! (see also \ref src/neuron/input_types)
#ifndef _SYNAPSE_TYPES_H_
#define _SYNAPSE_TYPES_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_row.h>

// Forward declaration of params type
struct synapse_types_params_t;
typedef struct synapse_types_params_t synapse_types_params_t;

// Forward declaration of real type
struct synapse_types_t;
typedef struct synapse_types_t synapse_types_t;

//! \brief initialise the structure from the parameters
//! \param[out] state: Pointer to the state to set up
//! \param[in] params: Pointer to the parameters passed in from host
//! \param[in] n_steps_per_timestep: The number of steps to run each update
static void synapse_types_initialise(synapse_types_t *state, synapse_types_params_t *params,
		uint32_t n_steps_per_time_step);

//! \brief save parameters and state back to SDRAM for reading by host and recovery
//!        on restart
//! \param[in] state: The current state
//! \param[out] params: Pointer to structure into which parameter can be written
static void synapse_types_save_state(synapse_types_t *state, synapse_types_params_t *params);

//! \brief decays the stuff thats sitting in the input buffers
//! as these have not yet been processed and applied to the neuron.
//!
//! This is to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly).
//! \param[in,out] parameters: the parameters to update
static void synapse_types_shape_input(synapse_types_t *parameters);

//! \brief adds the inputs for a give timer period to a given neuron that is
//!     being simulated by this model
//! \param[in] synapse_type_index: the type of input that this input is to be
//!     considered (aka excitatory or inhibitory etc)
//! \param[in,out] parameters: the parameters to update
//! \param[in] input: the inputs for that given synapse_type.
static void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_types_t *parameters,
        input_t input);

//! \brief extracts the excitatory input buffers from the buffers available
//!     for a given neuron ID
//! \param[in,out] excitatory_response: Buffer to put response in
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of excitatory input buffers for a given neuron ID.
static input_t* synapse_types_get_excitatory_input(
        input_t *excitatory_response, synapse_types_t *parameters);

//! \brief extracts the inhibitory input buffers from the buffers available
//!     for a given neuron ID
//! \param[in,out] inhibitory_response: Buffer to put response in
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of inhibitory input buffers for a given neuron ID.
static input_t* synapse_types_get_inhibitory_input(
        input_t *inhibitory_response, synapse_types_t *parameters);

//! \brief returns a human readable character for the type of synapse.
//! \details
//!     Examples would be `X` = excitatory types, `I` = inhibitory types, etc.
//! \param[in] synapse_type_index: the synapse type index
//!     (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static const char *synapse_types_get_type_char(index_t synapse_type_index);

//! \brief prints the parameters of the synapse type
//! \param[in] parameters: the pointer to the parameters to print
static void synapse_types_print_parameters(synapse_types_t *parameters);

//! \brief prints the input for a neuron ID given the available inputs
//!     currently only executed when the models are in debug mode, as the prints
//!     are controlled from the synapses.c print_inputs() method.
//! \param[in] parameters: the pointer to the parameters to print
static void synapse_types_print_input(synapse_types_t *parameters);

#endif // _SYNAPSE_TYPES_H_
