/*
 * Copyright (c) 2020 The University of Manchester
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
//! \brief Spike processing fast API
#ifndef _SPIKE_PROCESSING_FAST_H_
#define _SPIKE_PROCESSING_FAST_H_

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>
#include <spin1_api.h>
#include "synapse_row.h"
#include "synapse_provenance.h"

//! A region of SDRAM used to transfer synapses
struct sdram_config {
    //! The address of the input data to be transferred
    uint32_t *address;
    //! The size of the input data to be transferred
    uint32_t size_in_bytes;
    //! The time of the transfer in us
    uint32_t time_for_transfer;
};

//! The key and mask being used to send spikes from neurons processed on this
//! core.
struct key_config {
    //! The key
    uint32_t key;
    //! The mask
    uint32_t mask;
    //! The mask to get the spike ID
    uint32_t spike_id_mask;
    //! Is the node self connected
    uint32_t self_connected;
};

//! \brief Set up spike processing
//! \param[in] row_max_n_words The maximum row length in words
//! \param[in] spike_buffer_size The size to make the spike buffer
//! \param[in] discard_late_packets Whether to throw away packets not processed
//!                                 at the end of a time step or keep them for
//!                                 the next time step
//! \param[in] pkts_per_ts_rec_region The ID of the recording region to record
//!                                   packets-per-time-step to
//! \param[in] multicast_priority The priority of multicast processing
//! \param[in] sdram_inputs_param Details of the SDRAM transfer for the ring buffers
//! \param[in] ring_buffers_param The ring buffers to update with synapse weights
//! \return Whether the setup was successful or not
bool spike_processing_fast_initialise(
        uint32_t row_max_n_words, uint32_t spike_buffer_size,
        bool discard_late_packets, uint32_t pkts_per_ts_rec_region,
        uint32_t multicast_priority, struct sdram_config sdram_inputs_param,
        struct key_config key_config_param, weight_t *ring_buffers_param);

//! \brief The main loop of spike processing to be run once per time step.
//!        Note that this function will not return until the end of the time
//!        step; it will only be interrupted by SDP or MC packets.
void spike_processing_fast_time_step_loop(uint32_t time, uint32_t n_rewires);

//! \brief Store any provenance data gathered from spike processing
//! \param[in] prov The structure to store the provenance data in
void spike_processing_fast_store_provenance(struct synapse_provenance *prov);

//! \brief Called to tell the spike processing that the time step to record
//!        final data.
//! \param[in] The time step that has just finished.
void spike_processing_fast_pause(uint32_t time);

#endif // _SPIKE_PROCESSING_FAST_H_
