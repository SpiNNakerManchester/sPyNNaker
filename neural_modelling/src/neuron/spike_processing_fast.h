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

//! A region of SDRAM used to transfer synapses
struct sdram_config {
    //! The address of the input data to be transferred
    uint32_t *address;
    //! The size of the input data to be transferred
    uint32_t size_in_bytes;
    //! The time of the transfer in us
    uint32_t time_for_transfer_overhead;
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
    //! The colour shift to apply after masking
    uint32_t colour_shift;
    //! Is the node self connected
    uint32_t self_connected;
};

//! Provenance for spike processing
struct spike_processing_fast_provenance {
    //! A count of the times that the synaptic input circular buffers overflowed
    uint32_t n_input_buffer_overflows;
    //! The number of DMAs performed
    uint32_t n_dmas_complete;
    //! The number of spikes received and processed
    uint32_t n_spikes_processed;
    //! The number of rewirings performed.
    uint32_t n_rewires;
    //! The number of packets that were cleared at the end of timesteps
    uint32_t n_packets_dropped_from_lateness;
    //! The maximum size of the input buffer
    uint32_t max_filled_input_buffer_size;
    //! The maximum number of spikes received in a time step
    uint32_t max_spikes_received;
    //! The maximum number of spikes processed in a time step
    uint32_t max_spikes_processed;
    //! The number of times the transfer took longer than expected
    uint32_t n_transfer_timer_overruns;
    //! The number of times a time step was skipped entirely
    uint32_t n_skipped_time_steps;
    //! The maximum additional time taken to transfer
    uint32_t max_transfer_timer_overrun;
    //! The earliest received time of a spike
    uint32_t earliest_receive;
    //! The latest received time of a spike
    uint32_t latest_receive;
    //! The most spikes left at the end of any time step
    uint32_t max_spikes_overflow;
    //! SpiNNCer-related provenance
    //! The maximum number of spikes in a tick
    uint32_t max_spikes_in_a_tick;
    //! The maximum number of DMAs in a tick
    uint32_t max_dmas_in_a_tick;
    //! The maximum number of pipeline restarts
    uint32_t max_pipeline_restarts;
    //! Was the timer callback completed?
    uint32_t timer_callback_completed;
    //! Was the spike pipeline deactivated?
    uint32_t spike_pipeline_deactivated;
    //! The maximum number of flushed spikes in one step
    uint32_t max_flushed_spikes;
    //! Thet total number of flushed spikes
    uint32_t total_flushed_spikes;
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
//! \param[in] key_config_param Details of the key used by the neuron core
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
//! \param[in] time The time step of the simulation
//! \param[in] n_rewires The number of rewiring attempts to be done
void spike_processing_fast_time_step_loop(uint32_t time, uint32_t n_rewires);

//! \brief Store any provenance data gathered from spike processing
//! \param[in] prov The structure to store the provenance data in
void spike_processing_fast_store_provenance(
        struct spike_processing_fast_provenance *prov);

// Custom provenance from SpiNNCer

//! \brief get number of spikes received since last timer event
//! \return uint32_t number of spikes
void spike_processing_get_and_reset_spikes_this_tick(void);

//! \brief get number of dmas completed since last timer event
//! \return uint32_t number of DMAs
void spike_processing_get_and_reset_dmas_this_tick(void);

//! \brief get number of time pipeline was restarted since last timer event
//! \return uint32_t number of pipeline restarts
void spike_processing_get_and_reset_pipeline_restarts_this_tick(void);

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

#endif // _SPIKE_PROCESSING_FAST_H_
