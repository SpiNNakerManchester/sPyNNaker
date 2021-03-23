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

//! \file
//! \brief Spike processing API
#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>
#include <spin1_api.h>

//! \brief Initialise the spike processing system
//! \param[in] row_max_n_bytes: The maximum size of a synaptic row
//! \param[in] mc_packet_callback_priority:
//!     Multicast packet receive interrupt priority
//! \param[in] user_event_priority: User event interrupt priority
//! \param[in] incoming_spike_buffer_size: Size of buffer for receiving spikes
//! \param[in] packets_per_timestep_region:
//!     The recording region to use for the packets per timestep
//! \return True if initialisation succeeded
bool spike_processing_initialise(
        size_t row_max_n_bytes, uint mc_packet_callback_priority,
        uint user_event_priority, uint incoming_spike_buffer_size,
        bool clear_input_buffers_of_late_packets_init,
        uint32_t packets_per_timestep_region);

//! \brief Gets the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows(void);

//! \brief Gets the number of DMA's that were completed
//! \return the number of DMA's that were completed.
uint32_t spike_processing_get_dma_complete_count(void);

//! \brief Gets the number of spikes that were processed
//! \return the number of spikes that were processed
uint32_t spike_processing_get_spike_processing_count(void);

//! \brief Gets the number of successful rewires performed
//! \return the number of successful rewires
uint32_t spike_processing_get_successful_rewires(void);

//! \brief Set the number of times spike_processing has to attempt rewiring.
//! \param[in] number_of_rewires: The number of rewirings to perform
//! \return currently always true
bool spike_processing_do_rewiring(int number_of_rewires);

//! \brief return the number of packets dropped by the input buffer as they
//! arrived too late to be processed
//! \return the number of packets dropped.
uint32_t spike_processing_get_n_packets_dropped_from_lateness(void);

//! \brief clears the input buffer of packets
//! \param[in] time: The current timestep
void spike_processing_clear_input_buffer(timer_t time);

//! \brief returns how many packets were at max inside the input buffer at
//! any given point.
//! \return the max size the input buffer reached
uint32_t spike_processing_get_max_filled_input_buffer_size(void);

#endif // _SPIKE_PROCESSING_H_
