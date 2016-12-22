/*! \file
 * \brief implementation of synapse_types.h for Exponential shaping
*
* \details This is used to give a simple exponential decay to synapses.
*
* If we have combined excitatory/inhibitory synapses it will be
* because both excitatory and inhibitory synaptic time-constants
* (and thus propogators) are identical.
*/


#ifndef _SYNAPSE_TYPES_EXP_SUPERVISION_H_
#define _SYNAPSE_TYPES_EXP_SUPERVISION_H_

// This is currently used for decaying the neuron input
#include "../decay.h"

#include <debug.h>

// TODO: Determine the number of bits required by the synapse type in the
// synapse row data structure (i.e. enough bits to represent all desired
// synapse types)
// e.g. 1 bit for 2 possible types such as excitatory and inhibitory
// This must match the number returned by the python method
// get_n_synapse_type_bits
#define SYNAPSE_TYPE_BITS 2

// Only 1 of these is required for input - the 3rd type is for supervision only
#define SYNAPSE_INPUT_TYPE_BITS 1

// TODO: Determine the number of synapse types required
// (e.g. 2 for excitatory and inhibitory)]
// This must match the number returned by the python method
// get_n_synapse_types
#define SYNAPSE_TYPE_COUNT 3

// Only two of these types provide input - the 3rd type is for supervision only
#define SYNAPSE_INPUT_TYPE_COUNT 2

// TODO: Define the parameters required to compute the synapse shape
// The number of parameters here should match the number per neuron
// written by the python method write_synapse_parameters
typedef struct synapse_param_t {
    decay_t exc_decay;
    decay_t exc_init;
    decay_t inh_decay;
    decay_t inh_init;
} synapse_param_t;

// Include this here after defining the above items
#include "synapse_types.h"

// This makes it easy to keep track of which is which
typedef enum input_buffer_regions {
    EXCITATORY, INHIBITORY, SUPERVISION,
} input_buffer_regions;

//! \brief Shapes the values input into the neurons
//! \param[in-out] input_buffers the pointer to the input buffers to be shaped
//! \param[in] neuron_index the index of the neuron for which the value is to
//                          shaped
//! \param[in] parameters the synapse parameters passed in
//! \return nothing
static inline void synapse_types_shape_input(
        input_t *input_buffers, index_t neuron_index,
        synapse_param_t* parameters) {

    // The is the parameters for the neuron synapses
    synapse_param_t params = parameters[neuron_index];

    // Get the index of the excitatory synapse
    uint32_t ex_synapse_index = synapse_types_get_input_buffer_index(
        EXCITATORY, neuron_index);

    // Get the index of the inhibitory synapse
    uint32_t in_synapse_index = synapse_types_get_input_buffer_index(
        INHIBITORY, neuron_index);

    // TODO: Update the appropriate input buffers
    input_buffers[ex_synapse_index] = decay_s1615(input_buffers[ex_synapse_index],
                                                  params.exc_decay);
    input_buffers[in_synapse_index] = decay_s1615(input_buffers[in_synapse_index],
                                                  params.inh_decay);
}

//! \brief Adds the initial value to an input buffer for this shaping.  Allows
//         the input to be scaled before being added.
//! \param[in-out] input_buffers the pointer to the input buffers
//! \param[in] synapse_type_index the index of the synapse type to add the
//                                value to
//! \param[in] neuron_index the index of the neuron to add the value to
//! \param[in] parameters the synapse parameters passed in
//! \param[in] input the input to be added
//! \return None
static inline void synapse_types_add_neuron_input(
        input_t *input_buffers, index_t synapse_type_index,
        index_t neuron_index, synapse_param_t* parameters, input_t input) {
    use(parameters);

    // Get the index of the input being added to
    uint32_t input_index = synapse_types_get_input_buffer_index(
        synapse_type_index, neuron_index);

    if (synapse_type_index == EXCITATORY) {
        input_buffers[input_index] = input_buffers[input_index] + decay_s1615(input, parameters[neuron_index].exc_init);
    } else if (synapse_type_index == INHIBITORY) {
        input_buffers[input_index] = input_buffers[input_index] + decay_s1615(input, parameters[neuron_index].inh_init);
    }
}

//! \brief Gets the excitatory input for a given neuron
//! \param[in] input_buffers the pointer to the input buffers
//! \param[in] neuron_index the index of the neuron to be updated
//! \return the excitatory input value
static inline input_t synapse_types_get_excitatory_input(
        input_t *input_buffers, index_t neuron_index) {

    // TODO: Update to point to the correct synapse types for excitatory input
    uint32_t ex_synapse_index = synapse_types_get_input_buffer_index(
        EXCITATORY, neuron_index);
    return input_buffers[ex_synapse_index];
}

//! \brief Gets the inhibitory input for a given neuron
//! \param[in] input_buffers the pointer to the input buffers
//! \param[in] neuron_index the index of the neuron to be updated
//! \return the inhibitory input value
static inline input_t synapse_types_get_inhibitory_input(
        input_t *input_buffers, index_t neuron_index) {

    // TODO: Update to point to the correct synapse types for inhibitory input
    uint32_t in_synapse_index = synapse_types_get_input_buffer_index(
        INHIBITORY, neuron_index);
    return input_buffers[in_synapse_index];
}

//! \brief returns a human readable character for the type of synapse, for
//         debug purposes
//! examples would be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index the synapse type index
//! \return a human readable character representing the synapse type.
static inline const char *synapse_types_get_type_char(
        index_t synapse_type_index) {

    // TODO: Update with your synapse types
    if (synapse_type_index == EXCITATORY) {
        return "X";
    } else if (synapse_type_index == INHIBITORY)  {
        return "I";
    } else if (synapse_type_index == SUPERVISION) {
        return "S";
    } else {
        log_debug("did not recognise synapse type %i", synapse_type_index);
        return "?";
    }
}

//! \brief prints the input for a neuron id for debug purposes
//! \param[in] input_buffers the pointer to the input buffers
//! \param[in] neuron_index the id of the neuron to print the input for
//! \return Nothing
static inline void synapse_types_print_input(
        input_t *input_buffers, index_t neuron_index) {

    // TODO: Update to print your synapse types
    uint32_t ex_synapse_index = synapse_types_get_input_buffer_index(
            EXCITATORY, neuron_index);
    uint32_t in_synapse_index = synapse_types_get_input_buffer_index(
            INHIBITORY, neuron_index);
    io_printf(
        IO_BUF, "%12.6k - %12.6k",
        input_buffers[ex_synapse_index], input_buffers[in_synapse_index]);
}

static inline void synapse_types_print_parameters(synapse_param_t *parameters) {
    log_debug("exc_decay = %R\n", (unsigned fract) parameters->exc_decay);
    log_debug("exc_init  = %R\n", (unsigned fract) parameters->exc_init);
    log_debug("inh_decay = %R\n", (unsigned fract) parameters->inh_decay);
    log_debug("inh_init  = %R\n", (unsigned fract) parameters->inh_init);
}

#endif  // _SYNAPSE_TYPES_MY_IMPL_H_
