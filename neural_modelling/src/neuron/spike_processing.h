/*
 * Copyright (c) 2017-2019 The University of Manchester
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

#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>
#include <spin1_api.h>

bool spike_processing_initialise(
        size_t row_max_n_bytes, uint mc_packet_callback_priority,
        uint user_event_priority, uint incoming_spike_buffer_size);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows(void);

//! \brief set the number of times spike_processing has to attempt rewiring
//! \return bool: currently, always true
bool spike_processing_do_rewiring(int number_of_rew);

//! \brief get number of spikes received since last timer event
//! \return uint32_t number of spikes
uint32_t spike_processing_get_and_reset_spikes_this_tick();

//! \brief get number of dmas completed since last timer event
//! \return uint32_t number of DMAs
uint32_t spike_processing_get_and_reset_dmas_this_tick();

//! \brief get number of time pipeline was restarted since last timer event
//! \return uint32_t number of pipeline restarts
uint32_t spike_processing_get_and_reset_pipeline_restarts_this_tick();

//! \brief get time from T1 clock at which spike pipeline completed
//! \return uint32_t pipeline deactivation time
uint32_t spike_processing_get_pipeline_deactivation_time();

// FLUSH SPIKES
//! \brief returns the total unprocessed spikes from a simulation
//! \return total unprocessed spikes
uint32_t spike_processing_get_total_flushed_spikes();

//! \brief returns the maximum unprocessed spikes from a single
//! simulation timestep.
//! \return maximum unprocessed spikes from a single timestep.
uint32_t spike_processing_get_max_flushed_spikes();

#endif // _SPIKE_PROCESSING_H_
