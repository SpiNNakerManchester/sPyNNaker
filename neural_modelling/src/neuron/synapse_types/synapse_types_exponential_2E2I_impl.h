#ifndef _SYNAPSE_TYPES_EXPONENTIAL_2E2I_IMPL_H_
#define _SYNAPSE_TYPES_EXPONENTIAL_2E2I_IMPL_H_


//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 4

#define NUM_EXCITATORY_RECEPTORS 2
#define NUM_INHIBITORY_RECEPTORS 2

#include <neuron/decay.h>
#include <debug.h>
#include "synapse_types.h"


//---------------------------------------
// Synapse parameters
//---------------------------------------
input_t excitatory_response[NUM_EXCITATORY_RECEPTORS];
input_t inhibitory_response[NUM_INHIBITORY_RECEPTORS];

XXXXYYYYXXXX

typedef struct exp_params_t{
	decay_t decay;
    decay_t init;
    input_t synaptic_input_value;
}exp_params_t;

typedef struct synapse_param_t {
	exp_params_t exc;
	exp_params_t exc2;
	exp_params_t inh;
	exp_params_t inh2;
} synapse_param_t;

typedef enum input_buffer_regions {
    EXCITATORY, EXCITATORY2, INHIBITORY, INHIBITORY2,
} input_buffer_regions;


//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

//! \brief decays the stuff thats sitting in the input buffers
//! (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly) plus the
//! leaky aspect of a neuron). as these have not yet been processed and applied
//! to the neuron.
//! \param[in]  parameter: the pointer to the parameters to use
//! \return nothing
static inline void exp_shaping(exp_params_t* exp_params){

    // decay value according to decay constant
	exp_params->synaptic_input_value =
			decay_s1615(exp_params->synaptic_input_value,
					exp_params->decay);
}

static inline void set_to_zero(exp_params_t* exp_params){


    // this should only be called on exc2 -> to reset teacher input
	exp_params->synaptic_input_value = 0;

}

static inline void synapse_types_shape_input(
        synapse_param_pointer_t parameter) {

	exp_shaping(&parameter->exc);

//	exp_shaping(&parameter->exc2);
	set_to_zero(&parameter->exc2);

	exp_shaping(&parameter->inh);
	exp_shaping(&parameter->inh2);
}

//! \brief helper function to add input for a given timer period to a given
//! neuron
//! \param[in]  parameter: the pointer to the parameters to use
//! \param[in] input the inputs to add.
//! \return None
static inline void add_input_exp(exp_params_t* exp_params, input_t input){

	exp_params->synaptic_input_value = exp_params->synaptic_input_value +
			decay_s1615(input, exp_params->init);
}

//! \brief adds the inputs for a give timer period to a given neuron that is
//! being simulated by this model
//! \param[in] synapse_type_index the type of input that this input is to be
//! considered (aka excitatory or inhibitory etc)
//! \param[in]  parameter: the pointer to the parameters to use
//! \param[in] input the inputs for that given synapse_type.
//! \return None
static inline void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_param_pointer_t parameter,
        input_t input) {
	if (input > 0){
		if (synapse_type_index == EXCITATORY) {
			add_input_exp(&parameter->exc, input);

		} else if (synapse_type_index == EXCITATORY2) {
			add_input_exp(&parameter->exc2, input);

		} else if (synapse_type_index == INHIBITORY) {
			add_input_exp(&parameter->inh, input);

		} else if (synapse_type_index == INHIBITORY2) {
			add_input_exp(&parameter->inh2, input);
		}
	}
}

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given parameter set
//! \param[in]  parameter: the pointer to the parameters to use
//! \return the excitatory input buffers for a given neuron id.
static inline input_t* synapse_types_get_excitatory_input(
        synapse_param_pointer_t parameter) {
    excitatory_response[0] = parameter->exc.synaptic_input_value;
    excitatory_response[1] = parameter->exc2.synaptic_input_value;
    return &excitatory_response[0];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given parameter set
//! \param[in]  parameter: the pointer to the parameters to use
//! \return the inhibitory input buffers for a given neuron id.
static inline input_t* synapse_types_get_inhibitory_input(
        synapse_param_pointer_t parameter) {
    inhibitory_response[0] = parameter->inh.synaptic_input_value;
    inhibitory_response[1] = parameter->inh2.synaptic_input_value;
    return &inhibitory_response[0];
}

//! \brief returns a human readable character for the type of synapse.
//! examples would be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index the synapse type index
//! (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static inline const char *synapse_types_get_type_char(
        index_t synapse_type_index) {
    if (synapse_type_index == EXCITATORY) {
        return "X";
    } else if (synapse_type_index == INHIBITORY)  {
        return "X2";
    } else if (synapse_type_index == INHIBITORY)  {
            return "I";
    } else if (synapse_type_index == INHIBITORY)  {
        return "I2";
    } else {
        log_debug("did not recognise synapse type %i", synapse_type_index);
        return "?";
    }
}

//! \brief prints the input for a neuron id given the available inputs
//! currently only executed when the models are in debug mode, as the prints
//! are controlled from the synapses.c _print_inputs method.
//! \param[in]  parameter: the pointer to the parameters to use
//! \return Nothing
static inline void synapse_types_print_input(
        synapse_param_pointer_t parameter) {
    io_printf(
        IO_BUF, "%12.6k - %12.6k",
        parameter->exc.synaptic_input_value,
        parameter->inh.synaptic_input_value);
}

//! \brief printer call
//! \param[in] parameter: the pointer to the parameters to print
static inline void synapse_types_print_parameters(
        synapse_param_pointer_t parameter) {
    log_debug("exc_decay = %R\n", (unsigned fract) parameter->exc.decay);
    log_debug("exc_init  = %R\n", (unsigned fract) parameter->exc.init);
    log_debug("inh_decay = %R\n", (unsigned fract) parameter->inh.decay);
    log_debug("inh_init  = %R\n", (unsigned fract) parameter->inh.init);
    log_debug("gsyn_excitatory_initial_value = %11.4k\n",
              parameter->exc.synaptic_input_value);
    log_debug("gsyn_inhibitory_initial_value = %11.4k\n",
              parameter->inh.synaptic_input_value);
}

static inline void flush_synaptic_input(synapse_param_pointer_t parameter){
	 parameter->exc_a_response =  0.0k;
	 parameter->exc_b_response = 0.0k;
}


#endif  // _SYNAPSE_TYPES_EXPONENTIAL_2E2I_IMPL_H_
