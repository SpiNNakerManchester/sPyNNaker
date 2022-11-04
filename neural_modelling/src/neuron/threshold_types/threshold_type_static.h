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
//! \brief Threshold that fires at a fixed level
#ifndef _THRESHOLD_TYPE_STATIC_H_
#define _THRESHOLD_TYPE_STATIC_H_

#include "threshold_type.h"

struct threshold_type_params_t {
	//! The value of the static threshold
	REAL threshold_value;
};

//! Static threshold configuration
struct threshold_type_t {
    //! The value of the static threshold
    REAL threshold_value;
};

static void threshold_type_initialise(threshold_type_t *state,
		threshold_type_params_t *params, UNUSED uint32_t n_steps_per_timestep) {
	state->threshold_value = params->threshold_value;
}

static void threshold_type_save_state(UNUSED threshold_type_t *state,
		UNUSED threshold_type_params_t *params) {
}

//! \brief Determines if the value given is above the threshold value
//! \param[in] value: The value to determine if it is above the threshold
//! \param[in] threshold_type: The parameters to use to determine the result
//! \return True if the neuron should fire
static inline bool threshold_type_is_above_threshold(
        state_t value, threshold_type_t *threshold_type) {
    return REAL_COMPARE(value, >=, threshold_type->threshold_value);
}

#endif // _THRESHOLD_TYPE_STATIC_H_
