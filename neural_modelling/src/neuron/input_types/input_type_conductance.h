#ifndef _INPUT_TYPE_CONDUCTANCE_H_
#define _INPUT_TYPE_CONDUCTANCE_H_

#include "input_type.h"

typedef struct input_type_t {

    // reversal voltage - Excitatory [mV]
    REAL     V_rev_E;

    // reversal voltage - Inhibitory [mV]
    REAL     V_rev_I;
} input_type_t;

static inline input_t input_type_get_input_value(
        input_t value, input_type_pointer_t input_type) {
    use(input_type);
    return value >> 10;
}

static void input_type_set_inhibitory_multiplicator_value(
		input_t value, input_type_pointer_t input_type, input_t inh_input)
{
	use(value);
	use(input_type);
	use(inh_input);
}

static inline input_t input_type_convert_excitatory_input_to_current(
        input_t exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    return (exc_input * (input_type->V_rev_E - membrane_voltage));
}

static inline input_t input_type_convert_inhibitory_input_to_current(
	        input_t inh_input, input_type_pointer_t input_type,
	        state_t membrane_voltage) {
    return -(inh_input * (input_type->V_rev_I - membrane_voltage));
}

#endif // _INPUT_TYPE_CONDUCTANCE_H_
