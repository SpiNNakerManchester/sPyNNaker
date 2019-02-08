#ifndef _INPUT_TYPE_NONE_H_
#define _INPUT_TYPE_NONE_H_

#include "input_type.h"

typedef struct input_type_t {
} input_type_t;

static input_t* input_type_get_input_value(
        input_t* value, input_type_pointer_t input_type, uint16_t num_receptors) {
    use(value);
    use(input_type);
    use(num_receptors);
    return 0;
}

static void input_type_convert_excitatory_input_to_current(
        input_t* exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(exc_input);
    use(input_type);
    use(membrane_voltage);
}

static void input_type_convert_inhibitory_input_to_current(
        input_t* inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(inh_input);
    use(input_type);
    use(membrane_voltage);
}

#endif // _INPUT_TYPE_NONE_H_
