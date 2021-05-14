/*
 * Copyright (c) 2017-2020 The University of Manchester
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

#ifndef __SYNAPSE_PROVENANCE_H__
#define __SYNAPSE_PROVENANCE_H__

//! The provenance information for synaptic processing
struct synapse_provenance {
    //! A count of presynaptic events.
    uint32_t n_pre_synaptic_events;
    //! A count of synaptic saturations.
    uint32_t n_synaptic_weight_saturations;
    //! A count of the times that the synaptic input circular buffers overflowed
    uint32_t n_input_buffer_overflows;
    //! The number of STDP weight saturations.
    uint32_t n_plastic_synaptic_weight_saturations;
    //! The number of population table searches that had no match
    uint32_t n_ghost_pop_table_searches;
    //! The number of bit field reads that couldn't be read in due to DTCM limits
    uint32_t n_failed_bitfield_reads;
    //! The number of DMAs performed
    uint32_t n_dmas_complete;
    //! The number of spikes received and processed
    uint32_t n_spikes_processed;
    //! The number of population table searches that found an "invalid" entry
    uint32_t n_invalid_master_pop_table_hits;
    //! The number of spikes that a bit field filtered, stopping a DMA
    uint32_t n_filtered_by_bitfield;
    //! The number of rewirings performed.
    uint32_t n_rewires;
    //! The number of packets that were cleared at the end of timesteps
    uint32_t n_packets_dropped_from_lateness;
    //! The maximum size of the input buffer
    uint32_t spike_processing_get_max_filled_input_buffer_size;
};

#endif
