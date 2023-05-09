/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*!
 * \dir
 * \brief Neuronal Soma Models.
 * \file
 * \brief The API for neuron models themselves.
 */

#ifndef _NEURON_MODEL_H_
#define _NEURON_MODEL_H_

#include <common/neuron-typedefs.h>
#include <debug.h>

//! Forward declaration of neuron params type
struct neuron_params_t;
typedef struct neuron_params_t neuron_params_t;

//! Forward declaration of neuron type
struct neuron_t;
typedef struct neuron_t neuron_t;

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief initialise the structure from the parameters
//! \param[out] state: Pointer to the state to be filled in
//! \param[in] params: Pointer to the parameters passed in from host
//! \param[in] n_steps_per_timestep: Number of time steps to be done each full update
static void neuron_model_initialise(neuron_t *state, neuron_params_t *params,
		uint32_t n_steps_per_timestep);

//! \brief save parameters and state back to SDRAM for reading by host and recovery
//!        on restart
//! \param[in] state: The current state
//! \param[out] params: Pointer to structure into which parameter can be written
static void neuron_model_save_state(neuron_t *state, neuron_params_t *params);

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief primary function called in timer loop after synaptic updates
//! \param[in] num_excitatory_inputs: Number of excitatory receptor types.
//! \param[in] exc_input: Pointer to array of inputs per receptor type received
//!     this timer tick that produce a positive reaction within the neuron in
//!     terms of stimulation.
//! \param[in] num_inhibitory_inputs: Number of inhibitory receptor types.
//! \param[in] inh_input: Pointer to array of inputs per receptor type received
//!     this timer tick that produce a negative reaction within the neuron in
//!     terms of stimulation.
//! \param[in] external_bias: This is the intrinsic plasticity which could be
//!     used for ac, noisy input etc etc. (general purpose input)
//! \param[in] neuron the pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
//! \return state_t which is the value to be compared with a threshold value
//!     to determine if the neuron has spiked
static state_t neuron_model_state_update(
        uint16_t num_excitatory_inputs, input_t* exc_input,
        uint16_t num_inhibitory_inputs, input_t* inh_input,
        input_t external_bias, REAL current_offset, neuron_t *restrict neuron,
		REAL B_t);

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Indicates that the neuron has spiked
//! \param[in, out] neuron pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
static void neuron_model_has_spiked(neuron_t *restrict neuron);

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief get the neuron membrane voltage for a given neuron parameter set
//! \param[in] neuron: a pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
//! \return the membrane voltage for a given neuron with the neuron
//!     parameters specified in neuron
static state_t neuron_model_get_membrane_voltage(const neuron_t *neuron);

//! \brief printout of state variables i.e. those values that might change
//! \param[in] neuron: a pointer to a neuron parameter struct which contains all
//!     the parameters for a specific neuron
static void neuron_model_print_state_variables(const neuron_t *neuron);

//! \brief printout of parameters i.e. those values that don't change
//! \param[in] neuron: a pointer to a neuron parameter struct which contains all
//!     the parameters for a specific neuron
static void neuron_model_print_parameters(const neuron_t *neuron);

#endif // _NEURON_MODEL_H_
