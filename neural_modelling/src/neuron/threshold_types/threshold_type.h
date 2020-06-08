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

//! \dir
//! \brief Neuron firing thresholds
//! \file
//! \brief API for threshold types

#ifndef _THRESHOLD_TYPE_H_
#define _THRESHOLD_TYPE_H_

#include <common/neuron-typedefs.h>

// Forward declaration of the threshold pointer type
struct threshold_type_t;
typedef struct threshold_type_t threshold_type_t;
//! Pointer to a threshold type
typedef threshold_type_t* threshold_type_pointer_t;

//! \brief Determines if the value given is above the threshold value
//! \param[in] value: The value to determine if it is above the threshold
//! \param[in] threshold_type: The parameters to use to determine the result
//! \return True if the neuron should fire
static bool threshold_type_is_above_threshold(
        state_t value, threshold_type_t *threshold_type);

#endif // _THRESHOLD_TYPE_H_
