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
//! \brief Stochastic threshold, due to Wolfgang Maass _et al._
#ifndef _THRESHOLD_TYPE_STOCHASTIC_H_
#define _THRESHOLD_TYPE_STOCHASTIC_H_

#include "threshold_type.h"
#include <random.h>
#include <stdfix-exp.h>

//! Probability of firing when at saturation
#define PROB_SATURATION 0.8k

//! Stochastic threshold parameters
struct threshold_type_params_t {
    //! sensitivity of soft threshold to membrane voltage [mV<sup>-1</sup>]
    REAL     du_th;
    //! time constant for soft threshold [ms<sup>-1</sup>]
    REAL     tau_th;
    //! soft threshold value  [mV]
    REAL     v_thresh;
    //! time step scaling factor
    REAL     time_step_ms;
};

//! Stochastic threshold configuration
struct threshold_type_t {
    //! sensitivity of soft threshold to membrane voltage [mV<sup>-1</sup>]
    //! (inverted in python code)
    REAL     du_th_inv;
    //! time constant for soft threshold [ms<sup>-1</sup>]
    //! (inverted in python code)
    REAL     tau_th_inv;
    //! soft threshold value  [mV]
    REAL     v_thresh;
    //! time step scaling factor
    REAL     neg_machine_time_step_ms_div_10;
};

// HACK: Needed to make some versions of gcc not mess up
static volatile REAL ten = 10k;

static void threshold_type_initialise(threshold_type_t *state, threshold_type_params_t *params,
		uint32_t n_steps_per_timestep) {
	REAL ts = kdivui(params->time_step_ms, n_steps_per_timestep);
	state->du_th_inv = kdivk(ONE, params->du_th);
	state->tau_th_inv = kdivk(ONE, params->tau_th);
	state->v_thresh = params->v_thresh;
	state->neg_machine_time_step_ms_div_10 = kdivk(ts, ten);
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
    UREAL random_number = ukbits(mars_kiss64_simp() & 0xFFFF);

    REAL exponent = (value - threshold_type->v_thresh)
                    * threshold_type->du_th_inv;

    // if exponent is large, further calculation is unnecessary
    // (result --> prob_saturation).
    UREAL result;
    if (exponent < 5.0k) {
        REAL hazard = expk(exponent) * threshold_type->tau_th_inv;
        result = (1.0k - expk(hazard *
                threshold_type->neg_machine_time_step_ms_div_10)) *
                        PROB_SATURATION;
    } else {
        result = PROB_SATURATION;
    }

    return REAL_COMPARE(result, >=, random_number);
}

#endif // _THRESHOLD_TYPE_STOCHASTIC_H_
