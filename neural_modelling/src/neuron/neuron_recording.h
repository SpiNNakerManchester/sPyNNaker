/*
 * Copyright (c) 2019-2020 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _NEURON_RECORDING_H_
#define _NEURON_RECORDING_H_

#include <common/neuron-typedefs.h>

//! \brief returns how many variables are able to be recorded
//! \return the number of recordable variables
uint32_t neuron_recording_get_n_recorded_vars(void);

//! \brief allows neurons to wait till recordings have completed
void neuron_recording_wait_to_complete(void);

//! \brief stores a recording of a matrix based variable
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
void neuron_recording_set_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, state_t value);

//! \brief stores a recording of a matrix based double value
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
void neuron_recording_set_double_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, double value);

//! \brief stores a recording of a bitfield based variable
//! \param[in] neuron_index: which neuron to set the spike for
void neuron_recording_set_spike(uint32_t neuron_index);

//! \brief does the recording matrix process of handing over to basic recording
//! \param[in] time: the time stamp for this recording
void neuron_recording_matrix_record(uint32_t time);

//! \brief does the recording spikes process of handing over to basic recording
//! \param[in] time: the time stamp for this recording
//! \param[in] channel The channel to record spikes to
void neuron_recording_spike_record(uint32_t time, uint8_t spike_channel);

//! \brief sets up state for next recording.
void neuron_recording_setup_for_next_recording();

//! \brief reads recording data from sdram as reset.
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool neuron_recording_reset(address_t address, uint32_t n_neurons);

//! \brief sets up the recording stuff
//! \param[in] recording_address: sdram location for the recording data
//! \param[out] recording_flags: Output of flags which can be used to check if
//!            a channel is enabled for recording
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        address_t recording_address, uint32_t *recording_flags,
        uint32_t n_neurons);

//! \brief wrapper to recording finalise
void neuron_recording_finalise(void);

//! \brief wrapper to recording do time step update
//! \param[in] time: the time
void neuron_recording_do_timestep_update(uint32_t time);

#endif //_NEURON_RECORDING_H_
