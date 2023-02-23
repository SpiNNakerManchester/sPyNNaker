/*
 * Copyright (c) 2015 The University of Manchester
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

//! \file
//! \brief Input type is standard conductance-based model
#ifndef _INPUT_TYPE_CONDUCTANCE_H_
#define _INPUT_TYPE_CONDUCTANCE_H_

#include "input_type.h"
//#include "round.h"

//! Conductance input parameters
struct input_type_params_t {
    //! reversal voltage - Excitatory [mV]
    REAL     V_rev_E;
    //! reversal voltage - Inhibitory [mV]
    REAL     V_rev_I;
};

//! Conductance state
struct input_type_t {
    //! reversal voltage - Excitatory [mV]
    REAL     V_rev_E;
    //! reversal voltage - Inhibitory [mV]
    REAL     V_rev_I;
};

static inline void input_type_initialise(input_type_t *state, input_type_params_t *params,
		UNUSED uint32_t n_steps_per_timestep) {
	state->V_rev_E = params->V_rev_E;
	state->V_rev_I = params->V_rev_I;
}

static inline void input_type_save_state(UNUSED input_type_t *state,
		UNUSED input_type_params_t *params) {
}

//! \brief Gets the actual input value. This allows any scaling to take place
//! \param[in,out] value: The array of the receptor-based values of the input
//!     before scaling
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] num_receptors: The number of receptors.
//!     The size of the \p value array.
//! \return Pointer to array of values of the receptor-based input after
//!     scaling
static inline input_t *input_type_get_input_value(
        input_t *restrict value, UNUSED input_type_t *input_type,
        uint16_t num_receptors) {
    for (int i = 0; i < num_receptors; i++) {
        value[i] = value[i] >> 5;
    }
    return &value[0];
}

//! \brief Converts an excitatory input into an excitatory current
//! \param[in,out] exc_input: Pointer to array of excitatory inputs from
//!     different receptors this timestep. Note that this will already have
//!     been scaled by input_type_get_input_value()
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] membrane_voltage: The membrane voltage to use for the input
static inline void input_type_convert_excitatory_input_to_current(
        input_t *restrict exc_input, const input_type_t *input_type,
        state_t membrane_voltage) {
    for (int i=0; i < NUM_EXCITATORY_RECEPTORS; i++) {
        // accum = accum * (accum - accum)
        exc_input[i] = exc_input[i] *
                (input_type->V_rev_E - membrane_voltage);
        // RTN accum
//        exc_input[i] = MULT_ROUND_NEAREST_ACCUM(exc_input[i],
//                (input_type->V_rev_E - membrane_voltage));
    }
}

//! \brief Converts an inhibitory input into an inhibitory current
//! \param[in,out] inh_input: Pointer to array of inhibitory inputs from
//!     different receptors this timestep. Note that this will already have
//!     been scaled by input_type_get_input_value()
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] membrane_voltage: The membrane voltage to use for the input
static inline void input_type_convert_inhibitory_input_to_current(
        input_t *restrict inh_input, const input_type_t *input_type,
        state_t membrane_voltage) {
    for (int i=0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        // accum = accum * (accum - accum)
        inh_input[i] = -inh_input[i] *
                (input_type->V_rev_I - membrane_voltage);
        // RTN accum
//        inh_input[i] = MULT_ROUND_NEAREST_ACCUM(-inh_input[i],
//                (input_type->V_rev_I - membrane_voltage));
    }
}

#endif // _INPUT_TYPE_CONDUCTANCE_H_
