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

#include <common/in_spikes.h>
#include "synapses.h"
#include "spike_processing.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "direct_synapses.h"

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
    uint32_t n_ghost_pop_table_searches;
    uint32_t n_failed_bitfield_reads;
    uint32_t n_dmas_complete;
    uint32_t n_spikes_processed;
    uint32_t n_invalid_master_pop_table_hits;
    uint32_t n_filtered_by_bitfield;
    //! The number of rewirings performed.
    uint32_t n_rewires;
    uint32_t n_packets_dropped_from_lateness;
    uint32_t spike_processing_get_max_filled_input_buffer_size;
};

//! \brief Callback to store synapse provenance data (format: synapse_provenance).
//! \param[out] prov: The data structure to store the provenance data in
static inline void store_synapse_provenance(struct synapse_provenance *prov) {

    // store the data into the provenance data region
    prov->n_pre_synaptic_events = synapses_get_pre_synaptic_events();
    prov->n_synaptic_weight_saturations = synapses_saturation_count;
    prov->n_input_buffer_overflows = spike_processing_get_buffer_overflows();
    prov->n_plastic_synaptic_weight_saturations =
        synapse_dynamics_get_plastic_saturation_count();
    prov->n_ghost_pop_table_searches = ghost_pop_table_searches;
    prov->n_failed_bitfield_reads = failed_bit_field_reads;
    prov->n_dmas_complete = spike_processing_get_dma_complete_count();
    prov->n_spikes_processed = spike_processing_get_spike_processing_count();
    prov->n_invalid_master_pop_table_hits = invalid_master_pop_hits;
    prov->n_filtered_by_bitfield = bit_field_filtered_packets;
    prov->n_rewires = spike_processing_get_successful_rewires();
    prov->n_packets_dropped_from_lateness =
        spike_processing_get_n_packets_dropped_from_lateness();
    prov->spike_processing_get_max_filled_input_buffer_size =
        spike_processing_get_max_filled_input_buffer_size();
}

struct synapse_regions {
    uint32_t synapse_params;
    uint32_t direct_matrix;
    uint32_t pop_table;
    uint32_t synaptic_matrix;
    uint32_t synapse_dynamics;
    uint32_t structural_dynamics;
    uint32_t bitfield_filter;
};

struct synapse_priorities {
    uint32_t receive_packet;
    uint32_t process_synapses;
};

static inline bool initialise_synapse_regions(
        data_specification_metadata_t *ds_regions,
        struct synapse_regions regions, struct synapse_priorities priorities,
        uint32_t pkts_per_ts_rec_region) {
    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    bool clear_input_buffers_of_late_packets_init;
    uint32_t incoming_spike_buffer_size;
    uint32_t n_neurons;
    uint32_t n_synapse_types;
    if (!synapses_initialise(
            data_specification_get_region(regions.synapse_params, ds_regions),
            &n_neurons, &n_synapse_types,
            &ring_buffer_to_input_buffer_left_shifts,
            &clear_input_buffers_of_late_packets_init,
            &incoming_spike_buffer_size)) {
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
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(regions.pop_table, ds_regions),
            data_specification_get_region(regions.synaptic_matrix, ds_regions),
            direct_synapses_address, &row_max_n_words)) {
        return false;
    }
    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(regions.synapse_dynamics, ds_regions),
            n_neurons, n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // Set up structural plasticity dynamics
    if (!synaptogenesis_dynamics_initialise(data_specification_get_region(
            regions.structural_dynamics, ds_regions))) {
        return false;
    }

    if (!spike_processing_initialise(
            row_max_n_words, priorities.receive_packet,
            priorities.process_synapses, incoming_spike_buffer_size,
            clear_input_buffers_of_late_packets_init, pkts_per_ts_rec_region)) {
        return false;
    }

    // Do bitfield configuration last to only use any unused memory
    if (!population_table_load_bitfields(
            data_specification_get_region(regions.bitfield_filter, ds_regions))) {
        return false;
    }

    return true;
}
