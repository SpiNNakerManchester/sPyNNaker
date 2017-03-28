/*!  \file
 *  \brief interface for different types of synapse shaping.
 *
 *  \details    The API includes:
 *
 *     - synapse_types_get_input_buffer_index (synapse_type_index, neuron_index):
 *         helper method which returns the buffer index to which a given type
 *         of synapses are stored for a given neuron being simulated by the
 *         model.
 *     - synapse_types_shape_input(*input_buffers, neuron_index,  parameters):
 *     	   decays the stuff thats sitting in the input buffers (to compensate
 *     	   for the valve behaviour of a synapse in biology (spike goes in,
 *     	   synapse opens, then closes slowly)). as these have not yet been
 *     	   processed and applied to the neuron.
 *     - synapse_types_add_neuron_input(*input_buffers, synapse_type_index,
 *                                      neuron_index, parameters, input):
 *         adds the inputs for a give timer period to a given neuron that is
 *          being simulated by this model
 *     - synapse_types_get_excitatory_input (input_buffers, neuron_index)
 *          extracts the excitatory input buffers from the buffers available
 *           for a given neuron id
 *
 *     - synapse_types_get_inhibitory_input (input_buffers, neuron_index)
 *           extracts the inhibitory input buffers from the buffers available
 *           for a given neuron id
 *
 *     - synapse_types_get_type_char (synapse_type_index)
 *           returns a human readable character for the type of synapse.
 *           examples would be X = excitatory types, I = inhibitory types etc
 *           etc.
 *
 *     - synapse_types_print_input (input_buffers, neuron_index):
 *        prints the input for a neuron id given the available inputs currently
 *        only executed when the models are in debug mode, as the prints are
 *        controlled from the synapses.c _print_inputs method.
 * interface for all types of synapses shaping functions.
 */

#ifndef _SYNAPSE_TYPES_INTERFACE_
#define _SYNAPSE_TYPES_INTERFACE_

#include "common/neuron-typedefs.h"
#include "neuron/synapse_row.h"

//! \brief helper method which returns the buffer index to which a given type
//! of synapses are stored for a given neuron being simulated by the model.
//! \param[in] synapse_type_index the in the synapse row table which
//! corresponds to which type of synapse to look for.
//! NOTE: implementation HERE
//! \param[in] neuron_index the index of the neuron currently being considered
//! \return the position within a input buffer which contains the spikes that
//! will stimulate this neuron which are of a given synapse type.
static inline index_t synapse_types_get_input_buffer_index(
        index_t synapse_type_index, index_t neuron_index) {
    return ((synapse_type_index << SYNAPSE_INDEX_BITS) | neuron_index);
}

//! \brief decays the stuff thats sitting in the input buffers
//! (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly)).
//! as these have not yet been processed and applied to the neuron.
//! \param[in] input_buffers the pointer to the input buffers
//! \param[in] neuron_index the index in the neuron states which represent the
//! neuron currently being processed
//! \param[in] parameters the parameters retrieved from SDRAM which cover how
//! to initialise the synapse shaping rules.
//! \return nothing
static void synapse_types_shape_input(
    input_t *input_buffers, index_t neuron_index, synapse_param_t* parameters);

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
static void synapse_types_add_neuron_input(
    input_t *input_buffers, index_t synapse_type_index, index_t neuron_index,
    synapse_param_t* parameters, input_t input);

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the excitatory input buffers for a given neuron id.
static input_t synapse_types_get_excitatory_input(
    input_t *input_buffers, index_t neuron_index);

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given neuron id
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index the neuron id currently being considered
//! \return the inhibitory input buffers for a given neuron id.
static input_t synapse_types_get_inhibitory_input(
    input_t *input_buffers, index_t neuron_index);

//! \brief returns a human readable character for the type of synapse.
//! examples would be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index the synapse type index
//! (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static const char *synapse_types_get_type_char(index_t synapse_type_index);

//! \brief prints the parameters of the synapse type
//! \param[in] the pointer to the parameters to print
static void synapse_types_print_parameters(synapse_param_t *parameters);

//! \brief prints the input for a neuron id given the available inputs
//! currently only executed when the models are in debug mode, as the prints are
//! controlled from the synapses.c _print_inputs method.
//! \param[in] input_buffers the input buffers available
//! \param[in] neuron_index  the neuron id currently being considered
//! \return Nothing
static void synapse_types_print_input(
        input_t *input_buffers,  index_t neuron_index);

#endif // _SYNAPSE_TYPES_INTERFACE_
