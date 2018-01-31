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

#ifndef NUM_NEUROMODULATORS
#define NUM_NEUROMODULATORS 0
#error NUM_NEUROMODULATORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#include "input_type.h"

typedef struct input_type_t {

    // reversal voltage - Excitatory [mV]
    REAL     V_rev_E;

    // reversal voltage - Inhibitory [mV]
    REAL     V_rev_I;
} input_type_t;

// Receptor-independent shifts enabling individual scaling for different receptors
// ToDO Write these in input_type_t struct from Python to remove requirement to
// set manually.
// Note that this will cause problems if these arrays are not explicitly initialised
// when using multiple non-zero shifts.
uint16_t excitatory_shifts[NUM_EXCITATORY_RECEPTORS] = {10};
uint16_t inhibitory_shifts[NUM_INHIBITORY_RECEPTORS] = {10};

//---------------------------------------
// Functions called from timestep update in neuron.c
//---------------------------------------
// Deprecated - no longer required as scaling is applied when getting array of
// synaptic input.
static inline input_t input_type_get_input_value(
        input_t value, input_type_pointer_t input_type) {
    use(input_type);
    return value >> 10;
}

static inline input_t* input_type_convert_excitatory_input_to_current(
        input_t* exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {

    for (int i=0; i < NUM_EXCITATORY_RECEPTORS; i++){
    	exc_input[i] = (exc_input[i] >> //input_type->
        			excitatory_shifts[i]) *
					(input_type->V_rev_E - membrane_voltage);
    }

    return &exc_input[0];
}

static inline input_t* input_type_convert_inhibitory_input_to_current(
        input_t* inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {

    for (int i=0; i < NUM_INHIBITORY_RECEPTORS; i++){
    	inh_input[i] = -(inh_input[i] >> //input_type->
        	    	inhibitory_shifts[i]) *
					(input_type->V_rev_I - membrane_voltage);
    }

    return &inh_input[0];
}

#endif // _INPUT_TYPE_CONDUCTANCE_H_
