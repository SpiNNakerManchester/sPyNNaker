/*! \file
 *
 *  \brief interface for neurons
 *
 *  The API contains:
 *    - neuron_initialise(address, recording_flags, n_neurons_value):
 *         translate the data stored in the NEURON_PARAMS data region in SDRAM
 *         and converts it into c based objects for use.
 *    - neuron_set_input_buffers(input_buffers_value):
 *         setter for the internal input buffers
 *    - neuron_do_timestep_update(time):
 *         executes all the updates to neural parameters when a given timer
 *         period has occurred.
 */

#ifndef _NEURON_H_
#define _NEURON_H_

#include <common/neuron-typedefs.h>
#include "recording.h"

//! \brief translate the data stored in the NEURON_PARAMS data region in SDRAM
//!        and convert it into c based objects for use.
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[out] n_neurons_value Returns the number of neurons this model is to
//              simulate
//! \param[out] n_synapse_types_value Returns the number of synapse types in
//              the model
//! \param[out] incoming_spike_buffer_size Returns the number of spikes to
//!             support in the incoming spike buffer
//! \return boolean which is True if the translation was successful
//!         otherwise False
bool neuron_initialise(
    address_t address, uint32_t *n_neurons_value,
    uint32_t *n_synapse_types_value, uint32_t *incoming_spike_buffer_size);

//! \brief executes all the updates to neural parameters when a given timer
//!        period has occurred.
//! \param[in] time the timer tick value currently being executed
//! \return boolean which is True if the update succeded otherwise False
bool neuron_do_timestep_update(uint32_t time);

//! \brief interface for reloading neuron parameters as needed
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the reload of the neuron parameters was
//! successful or not
bool neuron_reload_neuron_parameters(address_t address);

//! \brief interface for rewriting the neuron parameters back into SDRAM
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
void neuron_store_neuron_parameters(address_t address);

//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index the index of the neuron
//! \param[in] weights_this_timestep weight inputs to be added
//! \return None
void neuron_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep);


#endif // _NEURON_H_
