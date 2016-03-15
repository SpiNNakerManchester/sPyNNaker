/*! \file
 * \brief implementation of synapse_types.h for Exponential shaping
*
* \details This is used to give a simple exponential decay to synapses.
*
* If we have combined excitatory/inhibitory synapses it will be
* because both excitatory and inhibitory synaptic time-constants
* (and thus propogators) are identical.
*
* This also includes a 'supervisor' synapse that provides a target spike time 
* and does NOT provide any postsynaptic neuron input
*/


#ifndef _SYNAPSE_TYPES_EXPONENTIAL_IMPL_H_
#define _SYNAPSE_TYPES_EXPONENTIAL_IMPL_H_

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 3

#include "../decay.h"
#include "../../common/out_spikes.h"
#include <debug.h>
#include <string.h>

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
    decay_t neuron_synapse_decay;
    decay_t neuron_synapse_init;
} synapse_param_t;

#include "synapse_types.h"
#include "../plasticity/synapse_dynamics.h"

typedef enum input_buffer_regions {
    EXCITATORY, INHIBITORY, TARGET,
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

//! \brief method which deduces how much decay to put on a excitatory input
//! (to compensate for the valve behaviour of a synapse in biology (spike goes
//! in, synapse opens, then closes slowly) plus the leaky aspect of a neuron).
//! \param[in] parameters the synapse parameters read from SDRAM to initialise
//! the synapse shaping.
//! \param[in] neuron_index the index in the neuron state array which
//! Corresponds to the parameters of the neuron currently being considered.
//! \return the decay amount for the excitatory input
static inline decay_t _ex_decay(
        synapse_param_t **parameters, index_t neuron_index) {
    return (parameters[0][neuron_index].neuron_synapse_decay);
}

//! \brief method which deduces how much decay to put on a inhibitory input
//! (to compensate for the valve behaviour of a synapse in biology (spike goes
//! in, synapse opens, then closes slowly) plus the leaky aspect of a neuron).
//! \param[in] parameters the synapse parameters read from SDRAM to initialise
//! the synapse shaping.
//! \param[in] neuron_index the index in the neuron state array which
//! Corresponds to the parameters of the neuron currently being considered.
//! \return the decay amount for the inhibitory input
static inline decay_t _in_decay(
        synapse_param_t **parameters, index_t neuron_index) {
    return (parameters[1][neuron_index].neuron_synapse_decay);
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
static inline void synapse_types_shape_input( input_t *input_buffers, 
    index_t neuron_index, synapse_param_t** parameters) {
    
    // decay the excitatory inputs
    input_buffers[_ex_offset(neuron_index)] = decay_s1615(
            input_buffers[_ex_offset(neuron_index)],
            _ex_decay(parameters, neuron_index));
    // decay the inhibitory inputs
    input_buffers[_in_offset(neuron_index)] = decay_s1615(
            input_buffers[_in_offset(neuron_index)],
            _in_decay(parameters, neuron_index));
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
    input_buffers[synapse_types_get_input_buffer_index(synapse_type_index,
        neuron_index)] += decay_s1615(input,
            parameters[synapse_type_index][neuron_index].neuron_synapse_init);
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
    } else if (synapse_type_index == INHIBITORY)  {
        return "I";
    } else if (synapse_type_index == TARGET)  {
        return "T";
    } else {
        log_debug("did not recognise synapse type %i", synapse_type_index);
        return "?";
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

#endif  // _SYNAPSE_TYPES_EXPONENTIAL_IMPL_H_
