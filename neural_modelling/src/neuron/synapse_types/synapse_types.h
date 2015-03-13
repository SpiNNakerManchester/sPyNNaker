#ifndef _SYNAPSE_TYPES_H_
#define _SYNAPSE_TYPES_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

static inline index_t synapse_types_get_input_buffer_index(
        index_t synapse_type_index, index_t neuron_index) {
    return ((synapse_type_index << SYNAPSE_INDEX_BITS) | neuron_index);
}

static void synapse_types_shape_input(
    input_t *input_buffers, index_t neuron_index, synapse_param_t** parameters);


static void synapse_types_add_neuron_input(
    input_t *input_buffers, index_t synapse_type_index, index_t neuron_index,
    synapse_param_t** parameters, input_t input);

//! \extracts the excitatory input buffers from the buffers available for a
//! given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the excitatory input buffers for a given neuron id.
static input_t synapse_types_get_excitatory_input(
    input_t *input_buffers, index_t neuron_index);

//! \extracts the inhibitory input buffers from the buffers available for a
//! given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the inhibitory input buffers for a given neuron id.
static input_t synapse_types_get_inhibitory_input(
    input_t *input_buffers, index_t neuron_index);

//! \returns a human readable character for the type of synapse. examples would
//! be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index the synapse type index
//! (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static const char *synapse_types_get_type_char(index_t synapse_type_index);

//! \ prints the input for a neuron id given the available inputs
//! currently only executed when the models are in debug mode, as the prints are
//! controlled from the synapses.c _print_inputs method.
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index  the neuron id currently being considered
//! \return Nothing
static void synapse_types_print_input(
		input_t *input_buffers,  index_t neuron_index);

#endif // _SYNAPSE_TYPES_H_
