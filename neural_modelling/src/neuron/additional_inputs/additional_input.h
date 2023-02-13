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
//! \brief Additional inputs to neuron models
//! \file
//! \brief API for additional inputs
#ifndef _ADDITIONAL_INPUT_TYPE_H_
#define _ADDITIONAL_INPUT_TYPE_H_

#include <common/neuron-typedefs.h>

// Forward declaration of the additional input parameters
struct additional_input_params_t;
typedef struct additional_input_params_t additional_input_params_t;

// Forward declaration of the additional input structure
struct additional_input_t;
typedef struct additional_input_t additional_input_t;

//! \brief initialise the structure from the parameters
//! \param[out] state: Pointer to the state to be set up
//! \param[in] params: Pointer to the parameters passed in from host
//! \param[in] n_steps_per_timestep: The number of steps to run each update
static void additional_input_initialise(
		additional_input_t *state, additional_input_params_t *params,
		uint32_t n_steps_per_timestep);

//! \brief save parameters and state back to SDRAM for reading by host and recovery
//!        on restart
//! \param[in] state: The current state
//! \param[out] params: Pointer to structure into which parameter can be written
static void additional_input_save_state(additional_input_t *state,
		additional_input_params_t *params);

//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage: The membrane voltage of the neuron
//! \return The value of the input after scaling
static input_t additional_input_get_input_value_as_current(
        struct additional_input_t *additional_input,
        state_t membrane_voltage);

//! \brief Notifies the additional input type that the neuron has spiked
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
static void additional_input_has_spiked(
        struct additional_input_t *additional_input);

#endif // _ADDITIONAL_INPUT_TYPE_H_
