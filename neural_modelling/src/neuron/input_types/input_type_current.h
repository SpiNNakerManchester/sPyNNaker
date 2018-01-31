#ifndef _INPUT_TYPE_CURRENT_H_
#define _INPUT_TYPE_CURRENT_H_

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

#ifndef NUM_NEUROMODULATORS
#define NUM_NEUROMODULATORS 0
#error NUM_NEUROMODULATORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#include "input_type.h"

typedef struct input_type_t {
} input_type_t;

// Receptor-independent shifts enabling individual scaling for different receptors
// ToDO Write these in input_type_t struct from Python to remove requirement to set manually
uint16_t excitatory_shifts[NUM_EXCITATORY_RECEPTORS] = {0};
uint16_t inhibitory_shifts[NUM_INHIBITORY_RECEPTORS] = {0};

//---------------------------------------
// Functions called from timestep update in neuron.c
//---------------------------------------
// Deprecated - no longer required as scaling is applied when getting array of
// synaptic input.
static inline input_t input_type_get_input_value(
        input_t value, input_type_pointer_t input_type) {
    use(input_type);
    return value;
}

static inline input_t* input_type_convert_excitatory_input_to_current(
        input_t* exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(input_type);
    use(membrane_voltage);

    for (int i=0; i < NUM_EXCITATORY_RECEPTORS; i++){
    	exc_input[i] = exc_input[i] >> //input_type->
        			excitatory_shifts[i];
    }

    return &exc_input[0];
}

static inline input_t* input_type_convert_inhibitory_input_to_current(
        input_t* inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {
    use(input_type);
    use(membrane_voltage);

    for (int i=0; i < NUM_INHIBITORY_RECEPTORS; i++){
    	inh_input[i] = inh_input[i] >> //input_type->
        	    	inhibitory_shifts[i];
    }

    return &inh_input[0];
}

#endif // _INPUT_TYPE_CURRENT_H_
