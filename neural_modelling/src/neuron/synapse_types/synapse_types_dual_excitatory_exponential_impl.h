/*! \file
*
* \brief implementation of synapse_types.h for a simple duel exponential decay
* to synapses.
*
* \details If we have combined excitatory_one/excitatory_two/inhibitory
* synapses it will be because both excitatory and inhibitory synaptic
* time-constants (and thus propogators) are identical.
*/

#ifndef _SYNAPSE_TYPES_DUAL_EXCITATORY_EXPONENTIAL_IMPL_H_
#define _SYNAPSE_TYPES_DUAL_EXCITATORY_EXPONENTIAL_IMPL_H_


//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 3

#define NUM_EXCITATORY_RECEPTORS 2
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

typedef struct synapse_param_t {
    decay_t exc_decay;
    decay_t exc_init;
    decay_t exc2_decay;
    decay_t exc2_init;
    decay_t inh_decay;
    decay_t inh_init;
    input_t input_buffer_excitatory_value;
    input_t input_buffer_excitatory2_value;
    input_t input_buffer_inhibitory_value;
} synapse_param_t;

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
    EXCITATORY_ONE, EXCITATORY_TWO, INHIBITORY,
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
static inline void synapse_types_shape_input(
        synapse_param_pointer_t parameter) {

    parameter->input_buffer_excitatory_value = decay_s1615(
        parameter->input_buffer_excitatory_value,
        parameter->exc_decay);
    parameter->input_buffer_excitatory2_value = decay_s1615(
        parameter->input_buffer_excitatory2_value,
        parameter->exc2_decay);
    parameter->input_buffer_inhibitory_value = decay_s1615(
        parameter->input_buffer_inhibitory_value,
        parameter->inh_decay);
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
    if (synapse_type_index == EXCITATORY_ONE) {
        parameter->input_buffer_excitatory_value =
            parameter->input_buffer_excitatory_value +
            decay_s1615(input, parameter->exc_init);

    } else if (synapse_type_index == EXCITATORY_TWO) {
        parameter->input_buffer_excitatory2_value =
            parameter->input_buffer_excitatory2_value +
            decay_s1615(input, parameter->exc2_init);

    } else if (synapse_type_index == INHIBITORY) {
        parameter->input_buffer_inhibitory_value =
            parameter->input_buffer_inhibitory_value +
            decay_s1615(input, parameter->inh_init);
    }
}

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given parameter set
//! \param[in]  parameter: the pointer to the parameters to use
//! \return the excitatory input buffers for a given neuron id.
static inline input_t* synapse_types_get_excitatory_input(
        synapse_param_pointer_t parameter) {
	excitatory_response[0] = parameter->input_buffer_excitatory_value;
	excitatory_response[1] = parameter->input_buffer_excitatory2_value;
    return &excitatory_response[0];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given parameter set
//! \param[in]  parameter: the pointer to the parameters to use
//! \return the inhibitory input buffers for a given neuron id.
static inline input_t* synapse_types_get_inhibitory_input(
        synapse_param_pointer_t parameter) {
	inhibitory_response[0] = parameter->input_buffer_inhibitory_value;
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
    } else if (synapse_type_index == INHIBITORY) {
        return "I";
    } else {
        log_debug("did not recognise synapse type %i", synapse_type_index);
        return "?";
    }
}

//! \brief prints the input for a neuron id given the available inputs
//! currently only executed when the models are in debug mode, as the prints are
//! controlled from the synapses.c _print_inputs method.
//! \param[in]  parameter: the pointer to the parameters to use
//! \return Nothing
static inline void synapse_types_print_input(
        synapse_param_pointer_t parameter) {
    io_printf(
        IO_BUF, "%12.6k + %12.6k - %12.6k",
        parameter->input_buffer_excitatory_value,
        parameter->input_buffer_excitatory2_value,
        parameter->input_buffer_inhibitory_value);
}

//! \brief printer call
//! \param[in] parameter: the pointer to the parameters to print
static inline void synapse_types_print_parameters(
        synapse_param_pointer_t parameter) {
    log_info("exc_decay  = %11.4k\n", parameter->exc_decay);
    log_info("exc_init   = %11.4k\n", parameter->exc_init);
    log_info("exc2_decay = %11.4k\n", parameter->exc2_decay);
    log_info("exc2_init  = %11.4k\n", parameter->exc2_init);
    log_info("inh_decay  = %11.4k\n", parameter->inh_decay);
    log_info("inh_init   = %11.4k\n", parameter->inh_init);
    log_info(
        "gsyn_excitatory_initial_value = %11.4k\n",
        parameter->input_buffer_excitatory_value);
    log_info(
        "gsyn_excitatory2_initial_value = %11.4k\n",
        parameter->input_buffer_excitatory2_value);
    log_info(
        "gsyn_inhibitory_initial_value = %11.4k\n",
        parameter->input_buffer_inhibitory_value);
}

#endif  // _SYNAPSE_TYPES_DUAL_EXCITATORY_EXPONENTIAL_IMPL_H_
