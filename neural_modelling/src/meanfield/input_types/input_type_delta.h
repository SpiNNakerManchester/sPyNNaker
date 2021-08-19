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

//! \file
//! \brief Input type shaped as Dirac delta
#ifndef _INPUT_TYPE_DELTA_H_
#define _INPUT_TYPE_DELTA_H_

#include "../../meanfield/input_types/input_type.h"

struct input_type_t {
	// scale factor (1000.0 / timestep)
	REAL scale_factor;
};

//! Scaling factor (trivial!) for input currents
static const REAL INPUT_SCALE_FACTOR = ONE;

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
        value[i] = value[i] * INPUT_SCALE_FACTOR;
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
        UNUSED state_t membrane_voltage) {
    for (int i=0; i < NUM_EXCITATORY_RECEPTORS; i++) {
        exc_input[i] = exc_input[i] * input_type->scale_factor;
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
        UNUSED state_t membrane_voltage) {
    for (int i=0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        inh_input[i] = inh_input[i] * input_type->scale_factor;
    }
}

#endif // _INPUT_TYPE_DELTA_H_
