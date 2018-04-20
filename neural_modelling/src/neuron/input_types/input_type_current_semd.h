#ifndef _INPUT_TYPE_CURRENT_SEMD_H_
#define _INPUT_TYPE_CURRENT_SEMD_H_

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
    // multiplicator
    REAL     multiplicator[NUM_INHIBITORY_RECEPTORS];

    // previous input value
    REAL     inh_input_previous[NUM_INHIBITORY_RECEPTORS];
} input_type_t;

input_t scaling_factor=40.0;

static inline input_t* input_type_get_input_value(
        input_t* value, input_type_pointer_t input_type, uint16_t num_receptors) {
    use(input_type);
    for (int i=0; i< num_receptors; i++){
    	value[i] = value[i];  // NOTE: this will be edited in future to be
    	                      //       multiplied by a scaling factor
    }
    return &value[0];
}

static void input_type_set_inhibitory_multiplicator_value(
		input_t* value, input_type_pointer_t input_type,
		input_t* inh_input) {
    for (int i=0; i<NUM_INHIBITORY_RECEPTORS; i++){
		if (inh_input[i] >= 0.01 && input_type->multiplicator[i]==0 &&
				input_type->inh_input_previous[i] == 0)
		{ input_type->multiplicator[i] = value[i]; }
		else if (inh_input[i] < 0.01)
		{ input_type->multiplicator[i] = 0; }

		input_type->inh_input_previous[i] = inh_input[i];
    }

}

static inline void input_type_convert_excitatory_input_to_current(
        input_t* exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(input_type);
    use(membrane_voltage);
    use(exc_input);
    //return exc_input;
}

static inline void input_type_convert_inhibitory_input_to_current(
        input_t* inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(membrane_voltage);

    // This changes inhibitory to excitatory input
    for (int i=0; i<NUM_INHIBITORY_RECEPTORS; i++){
    	inh_input[i] = (
    			-inh_input[i] * scaling_factor * input_type->multiplicator[i]);
    }
}

#endif // _INPUT_TYPE_CURRENT_SEMD_H_
