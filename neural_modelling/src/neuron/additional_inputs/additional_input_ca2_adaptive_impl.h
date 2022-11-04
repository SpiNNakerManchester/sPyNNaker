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
