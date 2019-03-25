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
//! \return boolean which is True if the translation was successful
//!         otherwise False
bool neuron_initialise(address_t address, uint32_t *timer_offset);

//! \brief executes all the updates to neural parameters when a given timer
//!        period has occurred.
//! \param[in] time the timer tick value currently being executed
//! \return nothing
bool neuron_do_timestep_update(
        uint32_t time, uint timer_count, uint timer_period);

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

#if LOG_LEVEL >= LOG_DEBUG
void neuron_print_inputs();

const char *neuron_get_synapse_type_char(uint32_t synapse_type);
#endif

#endif // _NEURON_H_
