#ifndef _SYNAPSE_TYPES_H_
#define _SYNAPSE_TYPES_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_row.h>


//! Forward declaration of synapse type (creates a definition for a pointer
//! to a synapse type parameter struct
typedef struct synapse_param_t* synapse_param_pointer_t;

//! \brief decays the stuff thats sitting in the input buffers
//! (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly)).
//! as these have not yet been processed and applied to the neuron.
//! \param[in]  parameters: the pointer to the parameters to use
//! \return nothing
static void synapse_types_shape_input(synapse_param_pointer_t parameter);

//! \brief adds the inputs for a give timer period to a given neuron that is
//! being simulated by this model
//! \param[in] synapse_type_index: the type of input that this input is to be
//! considered (aka excitatory or inhibitory etc)
//! \param[in] parameters: the pointer to the parameters to use
//! \param[in] input: the inputs for that given synapse_type.
//! \return None
static void synapse_types_add_neuron_input(
    index_t synapse_type_index, synapse_param_pointer_t parameter,
    input_t input);

//! \brief extracts the excitatory input buffers from the buffers available
//! for a given neuron ID
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of excitatory input buffers for a given neuron ID.
static input_t* synapse_types_get_excitatory_input(
    synapse_param_pointer_t parameter);

//! \brief extracts the inhibitory input buffers from the buffers available
//! for a given neuron ID
//! \param[in]  parameters: the pointer to the parameters to use
//! \return Pointer to array of inhibitory input buffers for a given neuron ID.
static input_t* synapse_types_get_inhibitory_input(
    synapse_param_pointer_t parameter);

//! \brief returns a human readable character for the type of synapse.
//! examples would be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index the synapse type index
//! (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static const char *synapse_types_get_type_char(index_t synapse_type_index);

//! \brief prints the parameters of the synapse type
//! \param[in] parameters: the pointer to the parameters to print
static void synapse_types_print_parameters(
    synapse_param_pointer_t parameters);

//! \brief prints the input for a neuron ID given the available inputs
//! currently only executed when the models are in debug mode, as the prints
//! are controlled from the synapses.c _print_inputs method.
//! \param[in] parameters: the pointer to the parameters to print
//! \return Nothing
static void synapse_types_print_input(synapse_param_pointer_t parameters);


// Enable operating on synaptic input on spike
static void flush_synaptic_input(synapse_param_pointer_t parameters);

#endif // _SYNAPSE_TYPES_H_
