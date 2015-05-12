/*! \file
*  \brief implementation of synapse_types.h for a alpha synpase shaping
*  (NOT TESTED)
*
*
*  Default values (iaf_psc_alpha.cpp/iaf_cond_exp.c)
*
* tau_x = 2.0ms  0.2ms
* tau_i = 2.0ms  2.0ms
*
* h current time step size in ms
*
* p11x = p22x = exp (-h/tau_x)
* p11i = p22i = exp (-h/tau_i)
*
* p21x = h * p11x
* p21i = h * p11i
*
* y2x  = p21x * y1x + p22x * y2x;
* y1x *= p11x
*
* y2i  = p21i * y1i + p22i * y2i;
* y1i *= p11i
*
* then add in current ring_buffer inputs..
*
* y1x +=  scale* ?  ring [n, x]
* y1i += scale* ?   ring [n, i]
* with scale 1/tau_x or tau_i as appropriate?
*/


#ifndef _SYNAPSE_TYPES_ALPHA_IMPL_H_
#define _SYNAPSE_TYPES_ALPHA_IMPL_H_

// TODO: Needs to be fixed to work correctly!

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 4

#include "synapse_types.h"
#include "../decay.h"
#include "../../common/constants.h"

typedef enum input_buffer_regions {
    EXCITATORY_ONE, EXCITATORY_TWO, INHIBITORY_ONE, INHIBITORY_TWO
} input_buffer_regions;


//! \brief check that the magic number handed to the shaping code is valid
//! \param[in] shaping_magic_number the magic number to check
//! \return bool where true says its valid and false otherwise
static inline bool synapse_types_initialise(
        uint32_t shaping_magic_number){
    if (shaping_magic_number == SYNAPSE_SHAPING_ALPHA_MAGIC_NUMBER){
        return true;
    }
    log_error("expected magic number 0x%x, got magic number 0x%x instead.",
                  SYNAPSE_SHAPING_ALPHA_MAGIC_NUMBER, shaping_magic_number);
    return false;
}

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

//! \brief helper method to make lower code more human readable
//! \param[in] neuron_index the index of the neuron in the neuron state array
//! which is currently being considered.
//! \return the offset position within the input buffer which points to the
//! input of the excitatory one inputs for a given neuron
static inline index_t _ex1_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(EXCITATORY_ONE, neuron_index);
}

//! \brief helper method to make lower code more human readable
//! \param[in] neuron_index the index of the neuron in the neuron state array
//! which is currently being considered.
//! \return the offset position within the input buffer which points to the
//! input of the inhibitory one inputs for a given neuron
static inline index_t _in1_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(INHIBITORY_ONE, neuron_index);
}

//! \brief helper method to make lower code more human readable
//! \param[in] neuron_index the index of the neuron in the neuron state array
//! which is currently being considered.
//! \return the offset position within the input buffer which points to the
//! input of the excitatory two inputs for a given neuron
static inline index_t _ex2_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(EXCITATORY_TWO, neuron_index);
}

//! \brief helper method to make lower code more human readable
//! \param[in] neuron_index the index of the neuron in the neuron state array
//! which is currently being considered.
//! \return the offset position within the input buffer which points to the
//! input of the inhibitory two inputs for a given neuron
static inline index_t _in2_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(INHIBITORY_TWO, neuron_index);
}

//! \brief method which deduces how much decay to put on a excitatory one input
//! (to compensate for the valve behaviour of a synapse in biology (spike goes
//! in, synapse opens, then closes slowly) plus the leaky aspect of a neuron).
//! \param[in] parameters the synapse parameters read from SDRAM to initialise
//! the synapse shaping.
//! \param[in] neuron_index the index in the neuron state array which
//! Corresponds to the parameters of the neuron currently being considered.
//! \return the decay amount for the excitatory one input
static inline decay_t _ex1_decay(
        synapse_param_t *parameters, index_t neuron_index) {
    return (parameters[EXCITATORY_ONE][neuron_index].neuron_synapse_decay);
}

//! \brief method which deduces how much decay to put on a inhibitory one input
//! (to compensate for the valve behaviour of a synapse in biology (spike goes
//! in, synapse opens, then closes slowly) plus the leaky aspect of a neuron).
//! \param[in] parameters the synapse parameters read from SDRAM to initialise
//! the synapse shaping.
//! \param[in] neuron_index the index in the neuron state array which
//! Corresponds to the parameters of the neuron currently being considered.
//! \return the decay amount for the inhibitory one input
static inline decay_t _in1_decay(
        synapse_param_t *parameters, index_t neuron_index) {
    return (parameters[INHIBITORY_ONE][neuron_index].neuron_synapse_decay);
}

//! \brief method which deduces how much decay to put on a excitatory two input
//! (to compensate for the valve behaviour of a synapse in biology (spike goes
//! in, synapse opens, then closes slowly) plus the leaky aspect of a neuron).
//! \param[in] parameters the synapse parameters read from SDRAM to initialise
//! the synapse shaping.
//! \param[in] neuron_index the index in the neuron state array which
//! Corresponds to the parameters of the neuron currently being considered.
//! \return the decay amount for the excitatory two input
static inline decay_t _ex2_decay(
        synapse_param_t *parameters, index_t neuron_index) {
    return (parameters[EXCITATORY_TWO][neuron_index].neuron_synapse_decay);
}

//! \brief method which deduces how much decay to put on a inhibitory two input
//! (to compensate for the valve behaviour of a synapse in biology (spike goes
//! in, synapse opens, then closes slowly) plus the leaky aspect of a neuron).
//! \param[in] parameters the synapse parameters read from SDRAM to initialise
//! the synapse shaping.
//! \param[in] neuron_index the index in the neuron state array which
//! Corresponds to the parameters of the neuron currently being considered.
//! \return the decay amount for the inhibitory two input
static inline decay_t _in2_decay(
        synapse_param_t *parameters, index_t neuron_index) {
    return (parameters[INHIBITORY_TWO][neuron_index].neuron_synapse_decay);
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
    // handle the excitatory inputs
    input_buffers[_ex2_offset(neuron_index)] =
        decay_s1615(input_buffers[_ex1_offset(neuron_index)],
                    _ex1_decay(parameters, neuron_index))
        + decay_s1615(input_buffers[_ex2_offset(neuron_index)],
                      _ex2_decay(parameters, neuron_index));
    // handle the inhibitory inputs
    input_buffers[_in2_offset(neuron_index)] =
            decay_s1615(input_buffers[_in1_offset(neuron_index)],
                        _in1_decay(parameters, neuron_index))
            + decay_s1615(input_buffers[_in2_offset(neuron_index)],
                          _in2_decay(parameters, neuron_index));
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
    input_buffers[
        synapse_types_get_input_buffer_index(synapse_type_index, neuron_index)]
            += decay_s1615(input, parameters[synapse_type_index]
                                            [neuron_index].neuron_synapse_init);
}

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the excitatory input buffers for a given neuron id.
static inline input_t synapse_types_get_excitatory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_ex2_offset(neuron_index)];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the inhibitory input buffers for a given neuron id.
static inline input_t synapse_types_get_inhibitory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_in2_offset(neuron_index)];
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
    } else if (synapse_type_index == EXCITATORY_TWO){
        return "X2";
    } else if (synapse_type_index == INHIBITORY_ONE){
        return "I1";
    } else if (synapse_type_index == INHIBITORY_TWO){
        return "I2";
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
    printf("%12.6k - %12.6k", input_buffers[_ex_offset(neuron_index)],
           input_buffers[_in_offset(neuron_index)]);
}


#endif  // _SYNAPSE_TYPES_ALPHA_IMPL_H_
