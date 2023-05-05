/*! \file
*
* \brief implementation of synapse_types.h for a simple duel exponential decay
* to synapses.
*
* \details If we have combined excitatory_one/excitatory_two/inhibitory
* synapses it will be because both excitatory and inhibitory synaptic
* time-constants (and thus propogators) are identical.
*/

#ifndef _SYNAPSE_TYPES_EPROP_ADPATIVE_IMPL_H_
#define _SYNAPSE_TYPES_EPROP_ADAPTIVE_IMPL_H_


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
//input_t excitatory_response[NUM_EXCITATORY_RECEPTORS];
//input_t inhibitory_response[NUM_INHIBITORY_RECEPTORS];

struct synapse_types_params_t {
	input_t exc;
	input_t exc2;
	input_t inh;
	input_t inh2;
//	REAL time_step_ms;
};

struct synapse_types_t {
    input_t exc;           //!< First excitatory synaptic input
    input_t exc2;          //!< Second excitatory synaptic input
    input_t inh;           //!< First inhibitory synaptic input
    input_t inh2;          //!< Second inhibitory synaptic input
};

//typedef struct synapse_param_t {
//    decay_t exc_decay;
//    decay_t exc_init;
//    decay_t exc2_decay;
//    decay_t exc2_init;
//    decay_t inh_decay;
//    decay_t inh_init;
//    decay_t inh2_decay;
//    decay_t inh2_init;
//    input_t input_buffer_excitatory_value;
//    input_t input_buffer_excitatory2_value;
//    input_t input_buffer_inhibitory_value;
//    input_t input_buffer_inhibitory2_value;
//} synapse_param_t;

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
    EXCITATORY_ONE, EXCITATORY_TWO, INHIBITORY_ONE, INHIBITORY_TWO
} input_buffer_regions;

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

static inline void synapse_types_initialise(synapse_types_t *state,
		synapse_types_params_t *params, UNUSED uint32_t n_steps_per_timestep) {
	state->exc = params->exc;
	state->exc2 = params->exc2;
	state->inh = params->inh;
	state->inh2 = params->inh2;
}

static inline void synapse_types_save_state(synapse_types_t *state,
		synapse_types_params_t *params) {
	params->exc = state->exc;
	params->exc2 = state->exc2;
	params->inh = state->inh;
	params->inh2 = state->inh2;
}

//! \brief decays the stuff thats sitting in the input buffers
//! (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly) plus the
//! leaky aspect of a neuron). as these have not yet been processed and applied
//! to the neuron.
//! \param[in]  parameter: the pointer to the parameters to use
//! \return nothing
static inline void synapse_types_shape_input(
        synapse_types_t *parameter) {

    parameter->exc = 0;
//    		decay_s1615(
//        parameter->input_buffer_excitatory_value,
//        parameter->exc_decay);
    parameter->exc2 = 0;
//    decay_s1615(
//        parameter->input_buffer_excitatory2_value,
//        parameter->exc2_decay);
    parameter->inh = 0;
//    decay_s1615(
//        parameter->input_buffer_inhibitory_value,
//        parameter->inh_decay);
    parameter->inh2 = 0;
//    decay_s1615(
//        parameter->input_buffer_inhibitory2_value,
//        parameter->inh2_decay);
}

//! \brief adds the inputs for a give timer period to a given neuron that is
//! being simulated by this model
//! \param[in] synapse_type_index the type of input that this input is to be
//! considered (aka excitatory or inhibitory etc)
//! \param[in]  parameter: the pointer to the parameters to use
//! \param[in] input the inputs for that given synapse_type.
//! \return None
static inline void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_types_t *parameter,
        input_t input) {
//    if (input){
//        io_printf(IO_BUF, "index = %u, %d \t input = %u, %d\t%u\n", synapse_type_index, synapse_type_index, input, input, input>>3);
//    }
    if (synapse_type_index == EXCITATORY_ONE) {
        parameter->exc += input;
//		=
//            parameter->input_buffer_excitatory_value +
//            decay_s1615(input, parameter->exc_init);

    } else if (synapse_type_index == EXCITATORY_TWO) {
        parameter->exc2 += input;
//		=
//            parameter->input_buffer_excitatory2_value +
//            decay_s1615(input, parameter->exc2_init);

    } else if (synapse_type_index == INHIBITORY_ONE) {
        parameter->inh += input;
//		=
//            parameter->input_buffer_inhibitory_value +
//            decay_s1615(input, parameter->inh_init);

    } else if (synapse_type_index == INHIBITORY_TWO) {
        parameter->inh2 += input;
//		=
//            parameter->input_buffer_inhibitory2_value +
//            decay_s1615(input, parameter->inh2_init);
    }
}

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given parameter set
//! \param[in]  parameter: the pointer to the parameters to use
//! \return the excitatory input buffers for a given neuron ID.
static inline input_t* synapse_types_get_excitatory_input(
		input_t *excitatory_response, synapse_types_t *parameter) {
    excitatory_response[0] = parameter->exc;
    excitatory_response[1] = parameter->exc2;
    return &excitatory_response[0];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given parameter set
//! \param[in]  parameter: the pointer to the parameters to use
//! \return the inhibitory input buffers for a given neuron ID.
static inline input_t* synapse_types_get_inhibitory_input(
		input_t *inhibitory_response, synapse_types_t *parameter) {
    inhibitory_response[0] = parameter->inh;
    inhibitory_response[1] = parameter->inh2;
    return &inhibitory_response[0];
}

//! \brief returns a human readable character for the type of synapse.
//! examples would be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index the synapse type index
//! (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static inline const char *synapse_types_get_type_char(
        index_t synapse_type_index) {
    if (synapse_type_index == EXCITATORY_ONE) {
        return "X1";
    } else if (synapse_type_index == EXCITATORY_TWO) {
        return "X2";
    } else if (synapse_type_index == INHIBITORY_ONE) {
        return "I1";
    } else if (synapse_type_index == INHIBITORY_TWO) {
        return "I2";
    } else {
        log_debug("did not recognise synapse type %i", synapse_type_index);
        return "?";
    }
}

//! \brief prints the input for a neuron ID given the available inputs
//! currently only executed when the models are in debug mode, as the prints are
//! controlled from the synapses.c _print_inputs method.
//! \param[in]  parameter: the pointer to the parameters to use
//! \return Nothing
static inline void synapse_types_print_input(
        synapse_types_t *parameter) {
    log_debug("%12.6k + %12.6k - %12.6k - %12.6k",
        parameter->exc, parameter->exc2,
        parameter->inh, parameter->inh2);
}

//! \brief printer call
//! \param[in] parameter: the pointer to the parameters to print
static inline void synapse_types_print_parameters(
        synapse_types_t *parameter) {
    log_debug("exc_init   = %11.4k\n", parameter->exc);
    log_debug("exc2_init  = %11.4k\n", parameter->exc2);
    log_debug("inh_init   = %11.4k\n", parameter->inh);
    log_debug("inh2_init   = %11.4k\n", parameter->inh2);
}

#endif  // _SYNAPSE_TYPES_ERBP_IMPL_H_
