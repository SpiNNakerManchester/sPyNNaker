#ifndef _THRESHOLD_TYPE_STOCHASTIC_H_
#define _THRESHOLD_TYPE_STOCHASTIC_H_

#include "threshold_type.h"
#include <random.h>
#include <stdfix-exp.h>

#define PROB_SATURATION 0.8k

struct threshold_type_t {
    // sensitivity of soft threshold to membrane voltage [mV^(-1)]
    // (inverted in python code)
    REAL     du_th_inv;
    // time constant for soft threshold [ms^(-1)]
    // (inverted in python code)
    REAL     tau_th_inv;
    // soft threshold value  [mV]
    REAL     v_thresh;
    //
    REAL     machine_time_step_ms_div_10;
};

static inline UREAL above_threshold_probability(
        state_t value, threshold_type_t *threshold_type) {
    REAL exponent = (value - threshold_type->v_thresh)
            * threshold_type->du_th_inv;

    // if exponent is large, further calculation is unnecessary
    // (result --> prob_saturation).
    if (exponent >= 5.0k) {
        return PROB_SATURATION;
    }

    REAL hazard = expk(exponent) * threshold_type->tau_th_inv;
    return (1.0k - expk(-hazard * threshold_type->machine_time_step_ms_div_10))
            * PROB_SATURATION;
}

static inline bool threshold_type_is_above_threshold(
        state_t value, threshold_type_t *threshold_type) {
    UREAL result = above_threshold_probability(value, threshold_type);
    UREAL random_number = ukbits(mars_kiss64_simp() & 0xFFFF);
    return REAL_COMPARE(result, >=, random_number);
}

#endif // _THRESHOLD_TYPE_STOCHASTIC_H_
