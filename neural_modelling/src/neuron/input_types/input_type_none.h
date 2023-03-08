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

//! \file
//! \brief The no-input input type
#ifndef _INPUT_TYPE_NONE_H_
#define _INPUT_TYPE_NONE_H_

#ifndef NUM_EXCITATORY_RECEPTORS
//! No inputs, so no receptors
#define NUM_EXCITATORY_RECEPTORS 0
#endif
#ifndef NUM_INHIBITORY_RECEPTORS
//! No inputs, so no receptors
#define NUM_INHIBITORY_RECEPTORS 0
#endif

#include "input_type.h"

struct input_type_params_t {
};

struct input_type_t {
};

static inline void input_type_initialise(UNUSED input_type_t *state,
		UNUSED input_type_params_t *params, UNUSED uint32_t n_steps_per_timestep) {
}

static inline void input_type_save_state(UNUSED input_type_t *state,
		UNUSED input_type_params_t *params) {
}

//! \brief Gets the actual input value. This allows any scaling to take place
//! \details Actually does nothing; no receptors
//! \param[in,out] value: The array of the receptor-based values of the input
//!     before scaling
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] num_receptors: The number of receptors.
//!     The size of the \p value array.
//! \return Pointer to array of values of the receptor-based input after
//!     scaling
static inline input_t *input_type_get_input_value(
        UNUSED input_t *restrict value, UNUSED input_type_t *input_type,
        UNUSED uint16_t num_receptors) {
    return 0;
}

//! \brief Converts an excitatory input into an excitatory current
//! \details Actually does nothing; no receptors
//! \param[in,out] exc_input: Pointer to array of excitatory inputs from
//!     different receptors this timestep. Note that this will already have
//!     been scaled by input_type_get_input_value()
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] membrane_voltage: The membrane voltage to use for the input
static inline void input_type_convert_excitatory_input_to_current(
        UNUSED input_t *restrict exc_input,
        UNUSED const input_type_t *input_type,
        UNUSED state_t membrane_voltage) {
}

//! \brief Converts an inhibitory input into an inhibitory current
//! \details Actually does nothing; no receptors
//! \param[in,out] inh_input: Pointer to array of inhibitory inputs from
//!     different receptors this timestep. Note that this will already have
//!     been scaled by input_type_get_input_value()
//! \param[in] input_type: The input type pointer to the parameters
//! \param[in] membrane_voltage: The membrane voltage to use for the input
static inline void input_type_convert_inhibitory_input_to_current(
        UNUSED input_t *restrict inh_input,
        UNUSED const input_type_t *input_type,
        UNUSED state_t membrane_voltage) {
}

#endif // _INPUT_TYPE_NONE_H_
