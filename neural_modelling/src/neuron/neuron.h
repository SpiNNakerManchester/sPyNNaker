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

#include "../common/neuron-typedefs.h"
#include "recording.h"

//! \brief translate the data stored in the NEURON_PARAMS data region in SDRAM
//!        and convert it into c based objects for use.
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] n_neurons_value The number of neurons this model is to emulate
//! \param[out] incoming_spike_buffer_size The number of spikes to support in
//!             the incoming spike buffer
//! \return boolean which is True is the translation was successful
//!         otherwise False
bool neuron_initialise(
    address_t address, uint32_t recording_flags, uint32_t *n_neurons_value,
    uint32_t *incoming_spike_buffer_size);

//! \setter for the internal input buffers
//! \param[in] input_buffers_value the new input buffers
//! \return None this method does not return anything.
void neuron_set_input_buffers(input_t *input_buffers_value);

//! \brief executes all the updates to neural parameters when a given timer period
//!        has occurred.
//! \param[in] time the timer tick value currently being executed
//! \return nothing
void neuron_do_timestep_update(uint32_t time);

#endif // _NEURON_H_
