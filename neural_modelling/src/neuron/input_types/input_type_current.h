#ifndef _INPUT_TYPE_CURRENT_H_
#define _INPUT_TYPE_CURRENT_H_

#include "input_type.h"

typedef struct input_type_t {
} input_type_t;

static inline input_t input_type_get_input_value(
        input_t value, input_type_pointer_t input_type) {
    use(input_type);
    return value;
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
    use(input_type);
    use(membrane_voltage);
    return inh_input;
}

#endif // _INPUT_TYPE_CURRENT_H_
