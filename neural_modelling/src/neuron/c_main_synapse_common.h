/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdbool.h>
#include <stdint.h>

#include <data_specification.h>
#include <common/in_spikes.h>
#include "synapses.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"

//! The region IDs used by synapse processing
struct synapse_regions {
    //! The parameters of the synapse processing
    uint32_t synapse_params;
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
    //! The number of synapses that were skipped due to late spikes
    uint32_t n_synapses_skipped;
    //! The number of spikes that were detected as late
    uint32_t n_late_spikes;
    //! The maximum lateness of a spike
    uint32_t max_late_spike;
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
    prov->n_synapses_skipped = skipped_synapses;
    prov->n_late_spikes = late_spikes;
    prov->max_late_spike = max_late_spike;
}

//! \brief Read data to set up synapse processing
//! \param[in] ds_regions: Pointer to region position data
//! \param[in] regions: The indices of the regions to be read
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
        struct synapse_regions regions, weight_t **ring_buffers,
        uint32_t *row_max_n_words,
        uint32_t *incoming_spike_buffer_size,
        bool *clear_input_buffer_of_late_packets,
        uint32_t *n_recording_regions_used) {
    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    uint32_t n_neurons;
    uint32_t n_synapse_types;
    if (!synapses_initialise(
            data_specification_get_region(regions.synapse_params, ds_regions),
            &n_neurons, &n_synapse_types, ring_buffers,
            &ring_buffer_to_input_buffer_left_shifts,
            clear_input_buffer_of_late_packets,
            incoming_spike_buffer_size)) {
        return false;
    }

    // Set up the population table
    if (!population_table_initialise(
            data_specification_get_region(regions.pop_table, ds_regions),
            data_specification_get_region(regions.synaptic_matrix, ds_regions),
            row_max_n_words)) {
        return false;
    }
    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(regions.synapse_dynamics, ds_regions),
            n_neurons, n_synapse_types, ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // Set up structural plasticity dynamics
    if (!synaptogenesis_dynamics_initialise(data_specification_get_region(
            regions.structural_dynamics, ds_regions), n_recording_regions_used)) {
        return false;
    }

    return true;
}
