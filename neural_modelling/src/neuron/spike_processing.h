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
#include "synapse_provenance.h"

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

void spike_processing_store_provenance(struct synapse_provenance *prov);

//! \brief Set the number of times spike_processing has to attempt rewiring.
//! \param[in] number_of_rewires: The number of rewirings to perform
//! \return currently always true
bool spike_processing_do_rewiring(int number_of_rewires);

//! \brief clears the input buffer of packets
//! \param[in] time: The current timestep
void spike_processing_clear_input_buffer(timer_t time);

#endif // _SPIKE_PROCESSING_H_
