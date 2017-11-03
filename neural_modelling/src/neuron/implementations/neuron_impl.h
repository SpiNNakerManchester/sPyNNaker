#ifndef _NEURON_IMPL_H_
#define _NEURON_IMPL_H_

#include "../../common/neuron-typedefs.h"

//! Forward declaration of the neuron impl pointer
typedef struct neuron_impl_t* neuron_impl_pointer_t;

//! \brief Initialise the particular implementation of the data
//! \param[in] data_address The address of the data to be initialised
//! \return None
static bool neuron_impl_initialise(uint32_t n_neurons);

//! \brief Add inputs as required to the implementation
//! \param[in] synapse_type_index the synapse type (exc. or inh.)
//! \param[in] parameter parameters for synapse shaping
//! \param[in] weights_this_timestep Weight inputs to be added
//! \return None
static void neuron_impl_add_inputs(
		index_t synapse_type_index, synapse_param_pointer_t parameter,
		input_t weights_this_timestep);

//! \brief Load in the neuron parameters... ?
//! \return None
static void neuron_impl_load_neuron_parameters(address_t data_address, uint32_t next);

//! \brief Wrapper to set global neuron parameters ?
//! \return None
static void neuron_impl_set_global_neuron_parameters();

//! \brief Do the timestep update for the particular implementation
//! \param[in] neuron index
//! \return bool value for whether a spike has occurred
static bool neuron_impl_do_timestep_update(timer_t time, index_t neuron_index);

//! \brief Communicate with parts of the model when spike occurs
//! \param[in] neuron index
//! \return None
static void neuron_impl_has_spiked(index_t neuron_index);

//! \setter for the internal input buffers
//! \param[in] input_buffers_value the new input buffers
static void neuron_impl_set_neuron_synapse_shaping_params(
		synapse_param_t *neuron_synapse_shaping_params_value);

//! \brief Wrapper for the neuron model's print state variables function
static void neuron_impl_print_state_variables(index_t neuron_index);

//! \brief Wrapper for the neuron model's print parameters function
static void neuron_impl_print_parameters(index_t neuron_index);

//! \brief Do any required recording
//! \param[in] recording_flags
//! \return None
static void neuron_impl_do_recording(timer_t time, uint32_t recording_flags);

//! \return The membrane voltage value
static input_t neuron_impl_get_membrane_voltage(index_t neuron_index);

#endif // _NEURON_IMPL_H_
