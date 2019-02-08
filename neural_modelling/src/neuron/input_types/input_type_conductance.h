#ifndef _INPUT_TYPE_CONDUCTANCE_H_
#define _INPUT_TYPE_CONDUCTANCE_H_

#ifndef NUM_EXCITATORY_RECEPTORS
#define NUM_EXCITATORY_RECEPTORS 1
#error NUM_EXCITATORY_RECEPTORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#ifndef NUM_INHIBITORY_RECEPTORS
#define NUM_INHIBITORY_RECEPTORS 1
#error NUM_INHIBITORY_RECEPTORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#include "input_type.h"

typedef struct input_type_t {

    // reversal voltage - Excitatory [mV]
    REAL     V_rev_E;

    // reversal voltage - Inhibitory [mV]
    REAL     V_rev_I;
} input_type_t;


static inline input_t* input_type_get_input_value(
        input_t* value, input_type_pointer_t input_type, uint16_t num_receptors) {
    use(input_type);
    for (int i = 0; i < num_receptors; i++) {
        value[i] = value[i] >> 10;
    }
    return &value[0];
}

static inline void input_type_convert_excitatory_input_to_current(
        input_t* exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {

    for (int i=0; i < NUM_EXCITATORY_RECEPTORS; i++){
        exc_input[i] = exc_input[i] *
                    (input_type->V_rev_E - membrane_voltage);
    }

}

static inline void input_type_convert_inhibitory_input_to_current(
        input_t* inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {

    for (int i=0; i < NUM_INHIBITORY_RECEPTORS; i++){
        inh_input[i] = -inh_input[i] *
                    (input_type->V_rev_I - membrane_voltage);
    }

}

#endif // _INPUT_TYPE_CONDUCTANCE_H_
