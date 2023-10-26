/*
 * Copyright (c) 2017 The University of Manchester
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

/*! \file
*
* \brief Utilities for synapse types with exponential decays
*/

#include <stdfix-exp.h>
#include <neuron/decay.h>
#include "round.h"

//! The type of exponential decay parameters
typedef struct exp_params_t {
	//! The decay time constant
    REAL tau;
    //! The initial value
    REAL init_input;
} exp_params_t;

//! The type of exponential decay state
typedef struct exp_state_t {
    decay_t decay;                  //!< Decay multiplier per timestep
    decay_t init;                   //!< Initial decay factor
    input_t synaptic_input_value;   //!< The actual synaptic contribution
} exp_state_t;

//! \brief Calculate the exponential state from the exponential parameters
//! \param[out] state The state to initialise
//! \param[in] params The parameters to use to do the initialisation
//! \param[in] time_step_ms The time step of the simulation overall
//! \param[in] n_steps_per_timestep The sub-stepping of the simulation
static inline void decay_and_init(exp_state_t *state, exp_params_t *params,
		REAL time_step_ms, uint32_t n_steps_per_timestep) {
	REAL ts = kdivui(time_step_ms, n_steps_per_timestep);
	REAL ts_over_tau = kdivk(ts, params->tau);
	decay_t decay = expulr(-ts_over_tau);
	decay_t inv_decay = 1.0ulr - decay;
	REAL tau_over_ts = kdivk(params->tau, ts);
	decay_t init = decay_s1615_to_u032(tau_over_ts, inv_decay);
	state->decay = decay;
	state->init = init;
	state->synaptic_input_value = params->init_input;
}

//! \brief Shapes a single parameter
//! \param[in,out] exp_param: The parameter to shape
static inline void exp_shaping(exp_state_t *exp_param) {
    // decay value according to decay constant
//    exp_param->synaptic_input_value =
//            MULT_ROUND_STOCHASTIC_ACCUM(exp_param->synaptic_input_value,
//                    exp_param->decay);
	exp_param->synaptic_input_value =
			decay_s1615(exp_param->synaptic_input_value, exp_param->decay);
}

//! \brief helper function to add input for a given timer period to a given
//!     neuron
//! \param[in,out] parameter: the parameter to update
//! \param[in] input: the input to add.
static inline void add_input_exp(exp_state_t *parameter, input_t input) {
//    parameter->synaptic_input_value = parameter->synaptic_input_value +
//            MULT_ROUND_STOCHASTIC_ACCUM(input, parameter->init);
    parameter->synaptic_input_value = parameter->synaptic_input_value +
            decay_s1615(input, parameter->init);
}
