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

//! \dir
//! \brief Synaptic inputs
//! \file
//! \brief API for synaptic inputs (see also \ref src/neuron/synapse_types)
#ifndef _INPUT_TYPE_H_
#define _INPUT_TYPE_H_

#ifndef NUM_EXCITATORY_RECEPTORS
//! \private
//! \brief The number of excitatory receptors.
//! \details It should be defined by a synapse shaping include.
#define NUM_EXCITATORY_RECEPTORS 1
#error NUM_EXCITATORY_RECEPTORS was undefined.  It should be defined by a synapse\
    shaping include
#endif

#ifndef NUM_INHIBITORY_RECEPTORS
//! \private
//! \brief The number of inhibitory receptors.
//! \details It should be defined by a synapse shaping include.
#define NUM_INHIBITORY_RECEPTORS 1
#error NUM_INHIBITORY_RECEPTORS was undefined.  It should be defined by a synapse\
    shaping include
#endif

#include <common/neuron-typedefs.h>

// Forward declaration of the input type parameters
struct input_type_params_t;
typedef struct input_type_params_t input_type_params_t;

// Forward declaration of the input type structure
struct input_type_t;
typedef struct input_type_t input_type_t;

//! \brief initialise the structure from the parameters
//! \param[out] state: Pointer to the state to set up
//! \param[in] params: Pointer to the parameters passed in from host
//! \param[in] n_steps_per_timestep: The number of steps to perform each update
static void input_type_initialise(input_type_t *state, input_type_params_t *params,
		uint32_t n_steps_per_timestep);

//! \brief save parameters and state back to SDRAM for reading by host and recovery
//!        on restart
//! \param[in] state: The current state
//! \param[out] params: Pointer to structure into which parameter can be written
static void input_type_save_state(input_type_t *state, input_type_params_t *params);

//! \brief Gets the actual input value. This allows any scaling to take place
//! \param[in,out] value: The array of the receptor-based values of the input
//!     before scaling
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] num_receptors: The number of receptors.
//!     The size of the \p value array.
//! \return Pointer to array of values of the receptor-based input after
//!     scaling
static input_t *input_type_get_input_value(
        input_t *restrict value, input_type_t *input_type,
        uint16_t num_receptors);

//! \brief Converts an excitatory input into an excitatory current
//! \param[in,out] exc_input: Pointer to array of excitatory inputs from
//!     different receptors this timestep. Note that this will already have
//!     been scaled by input_type_get_input_value()
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] membrane_voltage: The membrane voltage to use for the input
static void input_type_convert_excitatory_input_to_current(
        input_t *restrict exc_input, const input_type_t *input_type,
        state_t membrane_voltage);

//! \brief Converts an inhibitory input into an inhibitory current
//! \param[in,out] inh_input: Pointer to array of inhibitory inputs from
//!     different receptors this timestep. Note that this will already have
//!     been scaled by input_type_get_input_value()
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] membrane_voltage: The membrane voltage to use for the input
static void input_type_convert_inhibitory_input_to_current(
        input_t *restrict inh_input, const input_type_t *input_type,
        state_t membrane_voltage);

#endif // _INPUT_TYPE_H_
