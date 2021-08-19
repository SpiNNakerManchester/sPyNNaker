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
//! \brief Stochastic threshold, due to Wolfgang Maass _et al._
#ifndef _THRESHOLD_TYPE_STOCHASTIC_H_
#define _THRESHOLD_TYPE_STOCHASTIC_H_

#include <random.h>
#include <stdfix-exp.h>
#include "../../meanfield/threshold_types/threshold_type.h"

//! Probability of firing when at saturation
#define PROB_SATURATION 0.8k

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
        result = (1. - expk(hazard *
                threshold_type->neg_machine_time_step_ms_div_10)) *
                        PROB_SATURATION;
    } else {
        result = PROB_SATURATION;
    }

    return REAL_COMPARE(result, >=, random_number);
}

#endif // _THRESHOLD_TYPE_STOCHASTIC_H_
