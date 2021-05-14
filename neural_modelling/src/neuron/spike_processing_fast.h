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

bool spike_processing_fast_initialise(
        uint32_t row_max_n_words, uint32_t spike_buffer_size,
        bool discard_late_packets, uint32_t pkts_per_ts_rec_region,
        struct sdram_config sdram_inputs_param, weight_t *ring_buffers_param);

void spike_processing_fast_time_step_loop(uint32_t time);

void spike_processing_fast_store_provenance(struct synapse_provenance *prov);

void spike_processing_fast_pause(uint32_t time);

#endif // _SPIKE_PROCESSING_FAST_H_
