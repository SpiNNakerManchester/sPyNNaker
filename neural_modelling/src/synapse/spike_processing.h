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
        uint user_event_priority, uint incoming_spike_buffer_size,
        bool has_plastic_synapses);

void spike_processing_finish_write(uint32_t process_id);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows(void);

//! DMA buffer structure combines the row read from SDRAM with
typedef struct dma_buffer {
    // Address in SDRAM to write back plastic region to
    address_t sdram_writeback_address;

    // Key of originating spike
    // (used to allow row data to be re-used for multiple spikes)
    spike_t originating_spike;

    uint32_t n_bytes_transferred;

    // Row data
    uint32_t *row;
} dma_buffer;

////! \brief get the address of the circular buffer used for buffering received
////! spikes before processing them
////! \return address of circular buffer
//rate_buffer get_rate_buffer(void);

//! \brief set the DMA status
//! \param[in] busy: bool
//! \return None
void set_dma_busy(bool busy);

//! \brief retrieve the DMA status
//! \return bool
bool get_dma_busy(void);

//! \brief set the number of times spike_processing has to attempt rewiring
//! \return bool: currently, always true
bool do_rewiring(int number_of_rew);

//! exposing this so that other classes can call it
void setup_synaptic_dma_read(void);

//! \brief has this core received any spikes since the last batch of rewires?
//! \return bool
bool received_any_spike(void);

uint32_t spike_processing_flush_in_buffer();

uint32_t spike_processing_read_cb_calls();

#endif // _SPIKE_PROCESSING_H_
