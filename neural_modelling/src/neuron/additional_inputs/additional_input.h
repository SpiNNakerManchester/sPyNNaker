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

#ifndef _ADDITIONAL_INPUT_TYPE_H_
#define _ADDITIONAL_INPUT_TYPE_H_

#include <common/neuron-typedefs.h>

//! Forward declaration of the additional input pointer
typedef struct additional_input_t* additional_input_pointer_t;

//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \param[in] additional_input The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage The membrane voltage of the neuron
//! \return The value of the input after scaling
static input_t additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage);

//! \brief Notifies the additional input type that the neuron has spiked
//! \param[in] additional_input The additional input type pointer to the
//!     parameters
static void additional_input_has_spiked(
        additional_input_pointer_t additional_input);

#endif // _ADDITIONAL_INPUT_TYPE_H_
