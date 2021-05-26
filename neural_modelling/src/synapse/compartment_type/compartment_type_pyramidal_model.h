#ifndef _COMPARTMENT_TYPE_PYRAMIDAL_MODEL_H_
#define _COMPARTMENT_TYPE_PYRAMIDAL_MODEL_H_

#include "compartment_type.h"
#include <round.h>
#include <common/rate_generator.h>

// Converts a rate to an input
static inline input_t convert_rate_to_input(uint32_t rate) {

	union {
        uint32_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (rate);

    return converter.output_type;
}

static inline REAL compute_input_rate(uint32_t rate) {

    return out_rate(convert_rate_to_input(rate));
}

static inline REAL get_input_current(REAL input, REAL weight) {

    return MULT_ROUND_STOCHASTIC_ACCUM(input, weight);
}

#endif //_COMPARTMENT_TYPE_PYRAMIDAL_MODEL_H_