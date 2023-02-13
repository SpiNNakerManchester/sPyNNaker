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

//----------------------------------------------------------------------------
//! \file
//! \brief Implementation of adaptive calcium ion additional input
//!
//! Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency adaptation of
//! a generalized leaky integrate-and-fire model neuron. _Journal of
//! Computational Neuroscience,_ 10(1), 25-45. doi:10.1023/A:1008916026143
//----------------------------------------------------------------------------
#ifndef _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
#define _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_

#include "additional_input.h"

//! The additional input is due to calcium ions
struct additional_input_params_t {
    //! Time constant of decay of i_ca2
    REAL    tau_ca2;
    //! Calcium current
    REAL    i_ca2;
    //! Influx of CA2 caused by each spike
    REAL    i_alpha;
    //! The time step of the simulation
    REAL    time_step;
};

//! The additional input is due to calcium ions
struct additional_input_t {
    //! exp(-(machine time step in ms) / (tau_ca2))
    REAL    exp_tau_ca2;
    //! Calcium current
    REAL    i_ca2;
    //! Influx of CA2 caused by each spike
    REAL    i_alpha;
};

static inline void additional_input_initialise(
		additional_input_t *state, additional_input_params_t *params,
		uint32_t n_steps_per_timestep) {
	REAL ts = kdivui(params->time_step, n_steps_per_timestep);
	state->exp_tau_ca2 = expk(-kdivk(ts, params->tau_ca2));
	state->i_ca2 = params->i_ca2;
	state->i_alpha = params->i_alpha;
}

static inline void additional_input_save_state(additional_input_t *state,
		additional_input_params_t *params) {
	params->i_ca2 = state->i_ca2;
}

//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage: The membrane voltage of the neuron
//! \return The value of the input after scaling
static inline input_t additional_input_get_input_value_as_current(
        additional_input_t *additional_input,
        UNUSED state_t membrane_voltage) {
    // Decay Ca2 trace
    additional_input->i_ca2 *= additional_input->exp_tau_ca2;

    // Return the Ca2
    return -additional_input->i_ca2;
}

//! \brief Notifies the additional input type that the neuron has spiked
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
static inline void additional_input_has_spiked(
        additional_input_t *additional_input) {
    // Apply influx of calcium to trace
    additional_input->i_ca2 += additional_input->i_alpha;
}

#endif // _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
