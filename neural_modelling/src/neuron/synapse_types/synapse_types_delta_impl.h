// Delta_shaping
//
// This is used to give a simple exponential decay to synapses.
//
// If we have combined excitatory/inhibitory synapses it will be
// because both excitatory and inhibitory synaptic time-constants
// (and thus propogators) are identical.


#ifndef _SYNAPSE_TYPES_DELTA_IMPL_H_
#define _SYNAPSE_TYPES_DELTA_IMPL_H_

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 1
#define SYNAPSE_TYPE_COUNT 2

#include <debug.h>

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
} synapse_param_t;

#include "synapse_types.h"

typedef enum input_buffer_regions {
	EXCITATORY, INHIBITORY,
} input_buffer_regions;

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

//! \brief helper method to make lower code more human readable
//! \param[in] neuron_index the index of the neuron in the neuron state array
//! which is currently being considered.
//! \return the offset position within the input buffer which points to the
//! input of the excitatory inputs for a given neuron
static inline index_t _ex_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(EXCITATORY, neuron_index);
}

//! \brief helper method to make lower code more human readable
//! \param[in] neuron_index the index of the neuron in the neuron state array
//! which is currently being considered.
//! \return the offset position within the input buffer which points to the
//! input of the inhibitory inputs for a given neuron
static inline index_t _in_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(INHIBITORY, neuron_index);
}

//! \brief decays the stuff thats sitting in the input buffers
//! (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly) plus the
//! leaky aspect of a neuron). as these have not yet been processed and applied
//! to the neuron.
//! \param[in] input_buffers the pointer to the input buffers
//! \param[in] neuron_index the index in the neuron states which represent the
//! neuron currently being processed
//! \param[in] parameters the parameters retrieved from SDRAM which cover how
//! to initialise the synapse shaping rules.
//! \return nothing
static inline void synapse_types_shape_input(
		input_t *input_buffers, index_t neuron_index,
		synapse_param_t** parameters) {
    use(parameters);
    input_buffers[_ex_offset(neuron_index)] = 0;
    input_buffers[_in_offset(neuron_index)] = 0;
}

//! \brief adds the inputs for a give timer period to a given neuron that is
//! being simulated by this model
//! \param[in] input_buffers the input buffers which contain the input feed for
//! the given neuron being updated
//! \param[in] synapse_type_index the type of input that this input is to be
//! considered (aka excitatory or inhibitory etc)
//! \param[in] neuron_index the neuron that is being updated currently.
//! \param[in] parameters the neuron shaping parameters for this given neuron
//! being updated.
//! \param[in] input the inputs for that given synapse_type.
//! \return None
static inline void synapse_types_add_neuron_input(
		input_t *input_buffers, index_t synapse_type_index,
		index_t neuron_index, synapse_param_t** parameters, input_t input) {
    use(parameters);
    input_buffers[synapse_types_get_input_buffer_index(synapse_type_index,
        neuron_index)] += input;
}

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the excitatory input buffers for a given neuron id.
static inline input_t synapse_types_get_excitatory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_ex_offset(neuron_index)];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the inhibitory input buffers for a given neuron id.
static inline input_t synapse_types_get_inhibitory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_in_offset(neuron_index)];
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
    } else if (synapse_type_index == INHIBITORY){
        return "I";
    } else{
    	log_debug("did not recognise synapse type %i", synapse_type_index);
    }
}

//! \brief prints the input for a neuron id given the available inputs
//! currently only executed when the models are in debug mode, as the prints are
//! controlled from the synapses.c _print_inputs method.
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index  the neuron id currently being considered
//! \return Nothing
static inline void synapse_types_print_input(
        input_t *input_buffers, index_t neuron_index) {
    io_printf(IO_BUF, "%12.6k - %12.6k",
              input_buffers[_ex_offset(neuron_index)],
              input_buffers[_in_offset(neuron_index)]);
}

#endif  // _SYNAPSE_TYPES_DELTA_IMPL_H_
