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

#include <stdbool.h>
#include <stdint.h>

#include <data_specification.h>
#include <common/in_spikes.h>
#include "synapses.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "direct_synapses.h"

//! The region IDs used by synapse processing
struct synapse_regions {
    //! The parameters of the synapse processing
    uint32_t synapse_params;
    //! The direct or single matrix to be copied to DTCM
    uint32_t direct_matrix;
    //! The table to map from keys to memory addresses
    uint32_t pop_table;
    //! The SDRAM-based matrix of source spikes to target neurons
    uint32_t synaptic_matrix;
    //! Configuration for STDP
    uint32_t synapse_dynamics;
    //! Configuration for structural plasticity
    uint32_t structural_dynamics;
    //! The filters to avoid DMA transfers of empty rows
    uint32_t bitfield_filter;
};

//! The provenance information for synaptic processing
struct synapse_provenance {
    //! A count of presynaptic events.
    uint32_t n_pre_synaptic_events;
    //! A count of synaptic saturations.
    uint32_t n_synaptic_weight_saturations;
    //! The number of STDP weight saturations.
    uint32_t n_plastic_synaptic_weight_saturations;
    //! The number of population table searches that had no match
    uint32_t n_ghost_pop_table_searches;
    //! The number of bit field reads that couldn't be read in due to DTCM limits
    uint32_t n_failed_bitfield_reads;
    //! The number of population table searches that found an "invalid" entry
    uint32_t n_invalid_master_pop_table_hits;
    //! The number of spikes that a bit field filtered, stopping a DMA
    uint32_t n_filtered_by_bitfield;
};

//! \brief Callback to store synapse provenance data (format: synapse_provenance).
//! \param[out] prov: The data structure to store the provenance data in
static inline void store_synapse_provenance(struct synapse_provenance *prov) {

    // store the data into the provenance data region
    prov->n_pre_synaptic_events = synapses_get_pre_synaptic_events();
    prov->n_synaptic_weight_saturations = synapses_saturation_count;
    prov->n_plastic_synaptic_weight_saturations =
        synapse_dynamics_get_plastic_saturation_count();
    prov->n_ghost_pop_table_searches = ghost_pop_table_searches;
    prov->n_failed_bitfield_reads = failed_bit_field_reads;
    prov->n_invalid_master_pop_table_hits = invalid_master_pop_hits;
    prov->n_filtered_by_bitfield = bit_field_filtered_packets;
}

//! \brief Read data to set up synapse processing
//! \param[in] ds_regions: Pointer to region position data
//! \param[in] regions: The indices of the regions to be read
//! \param[out] n_neruons: Pointer to receive the number of neurons
//! \param[out] n_synapse_types: Pointer to receive the number of synapse types
//! \param[out] ring_buffers: The ring buffers that will be used
//! \param[out] row_max_n_words: Pointer to receive the maximum number of words
//!                              in a synaptic row
//! \param[out] incoming_spike_buffer_size: Pointer to receive the size to make
//!                                         the spike input buffer
//! \param[out] clear_input_buffer_of_late_packets: Pointer to receive whether
//!                                                 to clear the input buffer
//!                                                 each time step
//! \param[in/out] n_recording_regions_used: Pointer to variable which starts
//!                                          as the next recording region to use
//!                                          and is updated with regions used here
//! \return a boolean indicating success (True) or failure (False)
static inline bool initialise_synapse_regions(
        data_specification_metadata_t *ds_regions,
        struct synapse_regions regions, uint32_t *n_neurons,
        uint32_t *n_synapse_types, weight_t **ring_buffers,
        uint32_t *row_max_n_words,
        uint32_t *incoming_spike_buffer_size,
        bool *clear_input_buffer_of_late_packets,
        uint32_t *n_recording_regions_used) {
    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    if (!synapses_initialise(
            data_specification_get_region(regions.synapse_params, ds_regions),
            n_neurons, n_synapse_types, ring_buffers,
            &ring_buffer_to_input_buffer_left_shifts,
            clear_input_buffer_of_late_packets,
            incoming_spike_buffer_size)) {
        return false;
    }

    // set up direct synapses
    address_t direct_synapses_address;
    if (!direct_synapses_initialise(
            data_specification_get_region(regions.direct_matrix, ds_regions),
            &direct_synapses_address)) {
        return false;
    }

    // Set up the population table
    if (!population_table_initialise(
            data_specification_get_region(regions.pop_table, ds_regions),
            data_specification_get_region(regions.synaptic_matrix, ds_regions),
            direct_synapses_address, row_max_n_words)) {
        return false;
    }
    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(regions.synapse_dynamics, ds_regions),
            *n_neurons, *n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // Set up structural plasticity dynamics
    if (!synaptogenesis_dynamics_initialise(data_specification_get_region(
            regions.structural_dynamics, ds_regions), n_recording_regions_used)) {
        return false;
    }

    return true;
}
