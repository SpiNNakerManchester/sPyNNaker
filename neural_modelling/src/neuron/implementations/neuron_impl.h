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

#ifndef _NEURON_IMPL_H_
#define _NEURON_IMPL_H_

#include "neuron_impl_base_api.h"

//! \brief Do the timestep update for the particular implementation
//! \param[in] neuron_index The index of the neuron to update
//! \param[in] external_bias External input to be applied to the neuron
//! \param[in/out] recorded_variable_values The values to potentially record
//! \return bool value for whether a spike has occurred
static bool neuron_impl_do_timestep_update(
        index_t neuron_index, input_t external_bias,
        state_t *recorded_variable_values);

#endif // _NEURON_IMPL_H_
