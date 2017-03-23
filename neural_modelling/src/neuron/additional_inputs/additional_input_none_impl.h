#ifndef _ADDITIONAL_INPUT_TYPE_NONE_H_
#define _ADDITIONAL_INPUT_TYPE_NONE_H_

#include "additional_input_interface.h"

typedef struct additional_input_t {
} additional_input_t;

static input_t additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage) {
    use(additional_input);
    use(membrane_voltage);
    return 0;
}

static void additional_input_has_spiked(
        additional_input_pointer_t additional_input) {
    use(additional_input);
}

#endif // _ADDITIONAL_INPUT_TYPE_NONE_H_
