#ifndef _COMPARTMENT_TYPE_US_MODEL_H_
#define _COMPARTMENT_TYPE_US_MODEL_H_

#include "compartment_type.h"

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

    return (convert_rate_to_input(rate) - 0.5k);
}

static inline REAL get_input_current(REAL input, REAL weight) {

    return input;
}

#endif //_COMPARTMENT_TYPE_US_MODEL_H_