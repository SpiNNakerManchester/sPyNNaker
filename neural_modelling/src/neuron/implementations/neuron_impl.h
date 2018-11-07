#ifndef _NEURON_IMPL_H_
#define _NEURON_IMPL_H_

#include <common/neuron-typedefs.h>

//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons The number of neurons
//! \return bool
static bool neuron_impl_initialise(uint32_t n_neurons);

//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index the index of the neuron
//! \param[in] weights_this_timestep weight inputs to be added
//! \return None
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep);

//! \brief Load in the neuron parameters
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons);

//! \brief Do the timestep update for the particular implementation
//! \param[in] neuron_index The index of the neuron to update
//! \param[in] external_bias External input to be applied to the neuron
//! \param[in/out] recorded_variable_values The values to potentially record
//! \return bool value for whether a spike has occurred
static bool neuron_impl_do_timestep_update(
    index_t neuron_index, input_t external_bias,
    state_t *recorded_variable_values);

//! \brief Store the neuron parameters to the given address
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons);

#endif // _NEURON_IMPL_H_
