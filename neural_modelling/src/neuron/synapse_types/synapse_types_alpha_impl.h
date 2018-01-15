/*! \file
 * \brief implementation of synapse_types.h for an alpha synapse behaviour
 */

#ifndef _ALPHA_SYNAPSE_H_
#define _ALPHA_SYNAPSE_H_


//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 1
#define SYNAPSE_TYPE_COUNT 2

#define NUM_EXCITATORY_RECEPTORS 1
#define NUM_INHIBITORY_RECEPTORS 1
#define NUM_NEUROMODULATORS 0

#include "../decay.h"
#include <debug.h>
#include "synapse_types.h"


//---------------------------------------
// Synapse parameters
//---------------------------------------
input_t excitatory_response[NUM_EXCITATORY_RECEPTORS];
input_t inhibitory_response[NUM_INHIBITORY_RECEPTORS];

typedef struct alpha_params{
	// buffer for linear term
	input_t lin_buff;

	// buffer for exponential term
	input_t exp_buff;

	// Inverse of tau pre-multiplied by dt
	input_t dt_divided_by_tau_sqr;

	// Exponential decay multiplier
	decay_t decay;
}alpha_params;

typedef struct synapse_param_t {
	alpha_params exc;
	alpha_params inh;
} synapse_param_t;

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
	EXCITATORY, INHIBITORY,
} input_buffer_regions;


//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------
static inline void _alpha_shaping(alpha_params* a_params){
	a_params->lin_buff = a_params->lin_buff + a_params->dt_divided_by_tau_sqr;

	// Update exponential buffer
	a_params->exp_buff = decay_s1615(
			a_params->exp_buff,
			a_params->decay);
}

// Synapse shaping - called every timestep to evolve PSC
static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
	_alpha_shaping(&parameter->exc);
	_alpha_shaping(&parameter->inh);

	/*log_info("lin: %12.6k, exp: %12.6k, comb: %12.6k",
			parameter->exc.lin_buff,
			parameter->exc.exp_buff,
			parameter->exc.lin_buff * parameter->exc.exp_buff); */
}

static inline void _add_input_alpha(alpha_params* a_params, input_t input){
	a_params->exp_buff = (a_params->exp_buff * input) + ONE;

	a_params->lin_buff = (a_params->lin_buff
			+ a_params->dt_divided_by_tau_sqr)
					* (ONE - ONE/a_params->exp_buff);
}

// Add input from ring buffer - zero if no spikes, otherwise one or more weights
static inline void synapse_types_add_neuron_input(
		index_t synapse_type_index,
		synapse_param_pointer_t parameter,
        input_t input){

	if (input > ZERO){
		if (synapse_type_index == EXCITATORY) {
				_add_input_alpha(&parameter->exc, input);

		} else if (synapse_type_index == INHIBITORY) {
				_add_input_alpha(&parameter->inh, input);
		}
	}
}

static inline input_t* synapse_types_get_excitatory_input(
		synapse_param_pointer_t parameter) {
	excitatory_response[0] = parameter->exc.lin_buff * parameter->exc.exp_buff;
	return &excitatory_response[0];
}

static inline input_t* synapse_types_get_inhibitory_input(
		synapse_param_pointer_t parameter) {
	inhibitory_response[0] = parameter->inh.lin_buff * parameter->inh.exp_buff;
	return &inhibitory_response[0];
}

static inline const char *synapse_types_get_type_char(
		index_t synapse_type_index) {
	if (synapse_type_index == EXCITATORY) {
		return "X";
	} else if (synapse_type_index == INHIBITORY) {
		return "I";
	} else {
		log_debug("did not recognise synapse type %i", synapse_type_index);
		return "?";
	}
}

static inline void synapse_types_print_input(
        synapse_param_pointer_t parameter) {
    io_printf(IO_BUF, "%12.6k - %12.6k",
    		parameter->exc.lin_buff * parameter->exc.exp_buff,
			parameter->inh.lin_buff * parameter->inh.exp_buff);
}

static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
    log_debug("-------------------------------------\n");
	log_debug("exc_response  = %11.4k\n", parameter->exc.lin_buff * parameter->exc.exp_buff);
	log_debug("inh_response  = %11.4k\n", parameter->inh.lin_buff * parameter->inh.exp_buff);
}

#endif // _ALPHA_SYNAPSE_H_
