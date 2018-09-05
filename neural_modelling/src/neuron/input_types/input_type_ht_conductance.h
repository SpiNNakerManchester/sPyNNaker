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

	// Reversal potentials
	REAL exc_rev_E[NUM_EXCITATORY_RECEPTORS]; // {ampa_rev_E, nmda_rev_E}
	REAL inh_rev_E[NUM_INHIBITORY_RECEPTORS]; // {gaba_a_rev_E, gaba_b_rev_E}

} input_type_t;

static inline s1615 _evaluate_v_effect(state_t v){
	s1615 v_dep = 0;
	v = (v + 32k) >> 7; // add 32 to shift into range where it has greater variation with v
	if (v > -0.625k){ // -0.625k)
		if (v <= 0.325k) {
			v_dep = 0.783385k +  v * (1.42433k + v * (-3.00206k
					+ v * (-3.70779k + v * (12.1412k + 15.3091k * v))));
		} else {
			v_dep = 1.0k;
		}
	} else {
		v_dep = 0.0k;
	}

	// log_info("v before: %k, v_dep: %k", v, v_dep);
	return v_dep;
}

static inline input_t* input_type_get_input_value(
        input_t* value, input_type_pointer_t input_type, uint16_t num_receptors) {
    use(input_type);
    for (int i=0; i< num_receptors; i++){
    	value[i] = value[i] >> 10;
    }
    return &value[0];
}

static inline void input_type_convert_excitatory_input_to_current(
        input_t* exc_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {

    for (int i=0; i < NUM_EXCITATORY_RECEPTORS; i++){

    	exc_input[i] = exc_input[i] *
					(input_type->exc_rev_E[i] - membrane_voltage);

    	if (i==1){
    		// Gate NMDA conductance by voltage
    		exc_input[i] = exc_input[i] * _evaluate_v_effect(membrane_voltage);
    	}

    }

}

static inline void input_type_convert_inhibitory_input_to_current(
        input_t* inh_input, input_type_pointer_t input_type,
        state_t membrane_voltage) {

    for (int i=0; i < NUM_INHIBITORY_RECEPTORS; i++){
//    	log_info("reversal pot: %k", input_type->inh_rev_E[i]);
    	inh_input[i] = -inh_input[i] *
					(input_type->inh_rev_E[i] - membrane_voltage);
    }

}

#endif // _INPUT_TYPE_CONDUCTANCE_H_
