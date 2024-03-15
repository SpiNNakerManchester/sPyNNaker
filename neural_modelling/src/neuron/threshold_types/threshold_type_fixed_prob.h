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
//! \brief Stochastic threshold with fixed probability when over a fixed voltage.
#ifndef _THRESHOLD_TYPE_FIXED_PROB_H_
#define _THRESHOLD_TYPE_FIXED_PROB_H_

#include "threshold_type.h"
#include <random.h>

//! Stochastic threshold parameters
struct threshold_type_params_t {
    //! The value of the static threshold
    REAL     threshold_value;
    //! The probability of spiking when the threshold has been crossed
    UREAL    prob;
    //! The random seed
    mars_kiss64_seed_t random_seed;
};

//! Stochastic threshold configuration
struct threshold_type_t {
	//! The value of the static threshold
	REAL     threshold_value;
	//! The probability of spiking when the threshold has been crossed
	uint32_t prob;
	//! The random seed
	mars_kiss64_seed_t random_seed;
};

static void threshold_type_initialise(threshold_type_t *state,
		threshold_type_params_t *params,
		UNUSED uint32_t n_steps_per_timestep) {
	state->threshold_value = params->threshold_value;
	state->prob = params->prob * 0xFFFFFFFF;
	spin1_memcpy(state->random_seed, params->random_seed, sizeof(mars_kiss64_seed_t));
	validate_mars_kiss64_seed(state->random_seed);
}

static void threshold_type_save_state(UNUSED threshold_type_t *state,
		UNUSED threshold_type_params_t *params) {
	spin1_memcpy(params->random_seed, state->random_seed, sizeof(mars_kiss64_seed_t));
}

static inline bool threshold_type_is_above_threshold(
        state_t value, threshold_type_t *threshold_type) {
	if (value >= threshold_type->threshold_value) {
		uint32_t random_number = mars_kiss64_seed(threshold_type->random_seed);
		return random_number < threshold_type->prob;
	}
	return false;
}

#endif  // _THRESHOLD_TYPE_FIXED_PROB_H_
