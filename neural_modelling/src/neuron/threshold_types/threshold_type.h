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

//! \dir
//! \brief Neuron firing thresholds
//! \file
//! \brief API for threshold types

#ifndef _THRESHOLD_TYPE_H_
#define _THRESHOLD_TYPE_H_

#include <common/neuron-typedefs.h>

// Forward declaration of the threshold params type
struct threshold_type_params_t;
typedef struct threshold_type_params_t threshold_type_params_t;

// Forward declaration of the threshold pointer type
struct threshold_type_t;
typedef struct threshold_type_t threshold_type_t;

//! \brief initialise the state from the parameters
//! \param[out] state: Pointer to the state to initialise
//! \param[in] params: Pointer to the parameters passed in from host
//! \param[in] n_steps_per_timestep: The number of steps to run each update
static void threshold_type_initialise(threshold_type_t *state, threshold_type_params_t *params,
		uint32_t n_steps_per_timestep);

//! \brief save parameters and state back to SDRAM for reading by host and recovery
//!        on restart
//! \param[in] state: The current state
//! \param[out] params: Pointer to structure into which parameter can be written
static void threshold_type_save_state(threshold_type_t *state, threshold_type_params_t *params);

//! \brief Determines if the value given is above the threshold value
//! \param[in] value: The value to determine if it is above the threshold
//! \param[in] threshold_type: The parameters to use to determine the result
//! \return True if the neuron should fire
static bool threshold_type_is_above_threshold(
        state_t value, threshold_type_t *threshold_type);

#endif // _THRESHOLD_TYPE_H_
