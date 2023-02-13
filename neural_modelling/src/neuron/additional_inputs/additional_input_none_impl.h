/*
 * Copyright (c) 2015-2023 The University of Manchester
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
//! \brief Implementation of "no-such-input" additional input
#ifndef _ADDITIONAL_INPUT_TYPE_NONE_H_
#define _ADDITIONAL_INPUT_TYPE_NONE_H_

#include "additional_input.h"

//! An empty additional input that makes no contribution
struct additional_input_params_t {

};

//! An empty additional input that makes no contribution
struct additional_input_t {
};

static inline void additional_input_initialise(
		UNUSED additional_input_t *state, UNUSED additional_input_params_t *params,
		UNUSED uint32_t n_steps_per_timestep) {
}

static inline void additional_input_save_state(UNUSED additional_input_t *state,
		UNUSED additional_input_params_t *params) {
}

//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \details Does nothing
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage: The membrane voltage of the neuron
//! \return The value of the input after scaling
static inline input_t additional_input_get_input_value_as_current(
        UNUSED additional_input_t *additional_input,
        UNUSED state_t membrane_voltage) {
    return 0;
}

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Notifies the additional input type that the neuron has spiked
//! \details Does nothing
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
static inline void additional_input_has_spiked(
        UNUSED additional_input_t *additional_input) {
}

#endif // _ADDITIONAL_INPUT_TYPE_NONE_H_
