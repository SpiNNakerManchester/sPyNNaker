#ifndef _INPUT_TYPE_CURRENT_SEMD_H_
#define _INPUT_TYPE_CURRENT_SEMD_H_

#include "input_type.h"

typedef struct input_type_t {
    // multiplicator
    REAL     multiplicator;

    // previous input value
    REAL     inh_input_previous;
} input_type_t;

input_t scaling_factor=40.0;

static inline input_t input_type_get_input_value(
        input_t value, input_type_pointer_t input_type) {
    use(input_type);
    return value;
}

static void input_type_set_inhibitory_multiplicator_value(
		input_t value, input_type_pointer_t input_type,
		input_t inh_input) {
	if (inh_input >= 0.01 && input_type->multiplicator==0 &&
			input_type->inh_input_previous == 0)
	{ input_type->multiplicator = value; }
	else if (inh_input < 0.01)
	{ input_type->multiplicator = 0; }

	input_type->inh_input_previous = inh_input;
}

static inline input_t input_type_convert_excitatory_input_to_current(
        input_t exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(input_type);
    use(membrane_voltage);
    return exc_input;
}

static inline input_t input_type_convert_inhibitory_input_to_current(
        input_t inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(membrane_voltage);

    // This changes inhibitory to excitatory input
    return (-inh_input * scaling_factor * input_type->multiplicator);
}

#endif // _INPUT_TYPE_CURRENT_SEMD_H_
