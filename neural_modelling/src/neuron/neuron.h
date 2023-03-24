/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*! \file
 *  \brief interface for neurons
 *
 *  The API contains:
 *    - neuron_initialise():
 *         translate the data stored in the NEURON_PARAMS data region in SDRAM
 *         and converts it into C-based objects for use.
 *    - neuron_set_input_buffers(input_buffers_value):
 *         setter for the internal input buffers
 *    - neuron_do_timestep_update():
 *         executes all the updates to neural parameters when a given timer
 *         period has occurred.
 */

#ifndef _NEURON_H_
#define _NEURON_H_

#include "synapse_row.h"
#include <common/neuron-typedefs.h>
#include <spin1_api.h>

//! \brief translate the data stored in the NEURON_PARAMS data region in SDRAM
//!        and convert it into c based objects for use.
//! \param[in] core_params_address: the absolute address in SDRAM for the start
//!            of the core parameters data region in SDRAM
//! \param[in] neuron_params_address: The absolute address in SDRAM for the
//!            start of the neuron parameters data region in SDRAM
//! \param[in] current_sources_address: The absolute address in SDRAM for the
//!            start of the current sources data region in SDRAM
//! \param[in] recording_address: the recording parameters in SDRAM
//!            (contains which regions are active and how big they are)
//! \param[in] initial_values_address: The address where initial values can be
//!            written to for later reading.
//! \param[out] n_rec_regions_used: The number of regions used by neuron recording
//! \return True if the translation was successful, otherwise False
bool neuron_initialise(
        void *core_params_address, void *neuron_params_address,
        void *current_sources_address, void *recording_address,
        void *initial_values_address, uint32_t *n_rec_regions_used);

//! \brief executes all the updates to neural parameters when a given timer
//!        period has occurred.
//! \param[in] time: the timer tick value currently being executed
//! \param[in] timer_count: used for detecting a wrapping timer
void neuron_do_timestep_update(timer_t time, uint timer_count);

//! \brief Prepare to resume simulation of the neurons
//! \param[in] time: The time of the resume
//! \return bool which is true if the resume was successful or not
bool neuron_resume(uint32_t time);

//! \brief Perform steps needed before pausing a simulation.
//! \details Stores neuron parameters back into SDRAM.
void neuron_pause(void);

//! \brief Add inputs to the neurons
//! \param[in] syns The inputs to be added; this is an array of size
//!                 n_synapse_types * 2^ceil(log_2(n_neurons)).
void neuron_transfer(weight_t *syns);

#if LOG_LEVEL >= LOG_DEBUG
//! \brief Print the inputs to the neurons.
//! \details Only available in debug mode.
void neuron_print_inputs(void);

//! \brief Print the neurons' synapse parameters.
//! \details Only available in debug mode.
void neuron_print_synapse_parameters(void);

//! \brief Get the synapse _type_ description character.
//! \details Only available in debug mode.
//! \param[in] synapse_type: The synapse type.
//! \return a single character that describes the synapse.
const char *neuron_get_synapse_type_char(uint32_t synapse_type);
#endif

#endif // _NEURON_H_
