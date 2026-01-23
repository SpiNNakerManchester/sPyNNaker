/*
 * Copyright (c) 2026 The University of Manchester
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

/*! \file
 * \brief A filter binary that filters incoming spikes based on a bitfield
 */
#include <simulation.h>
#include <data_specification.h>
#include <filter_info.h>
#include <circular_buffer.h>
#include <wfi.h>
#include <population_table/population_table.h>

enum {

    // This is the system region
    FILTER_REGION_SYSTEM = 0,

    // This is the configuration, as detailed below as filter_config_t
    FILTER_REGION_CONFIG = 1,

    // This is the bitfield region, holding a bitfield for each incoming key
    FILTER_REGION_BITFIELDS = 2,

    // This is the master population table region
    FILTER_REGION_POP_TABLE = 3,

    // Provenance data region
    FILTER_REGION_PROVENANCE = 4
} filter_regions_e;

typedef struct {
    // The mask to extract the application id from the incoming key
    uint32_t app_id_mask;
    // The shift to extract the application id from the incoming key
    uint32_t app_id_shift;
    // The minimum application id to accept
    uint32_t app_id_min;
    // The maximum application id to accept
    uint32_t app_id_max;
    // The size of input queue to use
    uint32_t input_queue_size;
    // The number of different targets to send to, round robin
    uint32_t n_targets;
    // The keys for each of the targets
    uint32_t send_keys[];
} filter_config_t;

typedef struct {
    //! The number of spikes received from the network
    uint32_t n_spikes_received;
    //! The number of spikes forwarded on to a core
    uint32_t n_spikes_forwarded;
    //! The number of spikes dropped due to invalid application ID (should be 0)
    uint32_t n_spikes_invalid_app_id;
    //! The number of times the spike input queue was full (these are lost)
    uint32_t n_times_queue_overflowed;
} filter_provenance_t;

typedef struct {
    //! The mask to get the source-core-local neuron ID.
    //! This can be computed from master_population_table_entry
    //!     ~(mask | (core_mask << core_shift))
    uint32_t mask: 12;
    //! Flag to indicate if the filter is redundant.
    //! This can be copied from filter_info_t.all_ones field
    uint32_t all_ones: 1;
    //! The number of bits of key used for colour (0 if no colour).
    //! This can be copied from master_population_table_entry.n_colour_bits
    uint32_t n_colour_bits: 3;
    //! The mask to apply to the key once shifted to get the core index.
    //! This can be copied from master_population_table_entry.core_mask
    uint32_t core_mask: 16;
    //! The shift to apply to the key to get the core part
    //! This can be copied from master_population_table_entry.mask_shift
    uint32_t core_shift: 16;
    //! The number of neurons per core
    //! This can be copied from master_population_table_entry.n_neurons
    uint32_t n_neurons: 16;
    //! The bit field itself (note bit_field_t is a pointer type)
    //! This can be copied from filter_info_t.data
    bit_field_t data;
} bit_field_filter_info_t;

static filter_config_t *config;

static circular_buffer input_queue;

static bit_field_filter_info_t *filters;

static filter_provenance_t prov;

static uint32_t next_target = 0;

static volatile bool running = false;

static inline bool check_app_id(uint32_t spike, uint32_t *app_id) {
    *app_id = (spike & config->app_id_mask) >> config->app_id_shift;
    return (app_id <= config->app_id_max) && (app_id >= config->app_id_min);
}

//! \brief Get the source core index from a spike
//! \param[in] filter: The filter info for the spike
//! \param[in] spike: The spike received
//! \return the source core index in the list of source cores
static inline uint32_t get_core_index(bit_field_filter_info_t filter,
        spike_t spike) {
    return (spike >> filter.core_shift) & filter.core_mask;
}

//! \brief Get the total number of neurons on cores which come before this core
//! \param[in] filter: The filter info for the spike
//! \param[in] spike: The spike received
//! \return the base neuron number of this core
static inline uint32_t get_core_sum(bit_field_filter_info_t filter,
        spike_t spike) {
    return get_core_index(filter, spike) * filter.n_neurons;
}

//! \brief Get the neuron id of the neuron on the source core
//! \param[in] filter: the filter info for the spike
//! \param[in] spike: the spike received
//! \return the source neuron id local to the core
static inline uint32_t get_local_neuron_id(bit_field_filter_info_t filter,
        spike_t spike) {
    return spike & filter.mask;
}

static inline bool accepted(uint32_t app_id, uint32_t spike) {
    uint32_t pos = app_id - config->app_id_min;
    bit_field_t bit_field = filters[pos].data;
    if (bit_field == NULL) {
        prov.n_spikes_invalid_app_id += 1;
        return false;
    }
    if (filters[pos].all_ones) {
        return true;
    }
    uint32_t neuron_id = get_core_sum(filters[pos], spike)
            + get_local_neuron_id(filters[pos], spike);
    return bit_field_get(bit_field, neuron_id);
}

static inline uint32_t get_key() {
    uint32_t target = next_target;
    next_target = (next_target + 1);
    if (next_target >= config->n_targets) {
        next_target = 0;
    }
    return config->send_keys[target];
}

static inline void process_spike(void) {
    uint32_t spike;
    circular_buffer_pop(input_queue, &spike);

    // Check against the bitfield
    uint32_t app_id;
    if (!check_app_id(spike, &app_id)) {
        // Not in range, drop
        prov.n_spikes_invalid_app_id += 1;
        continue;
    }

    // If accepted, forward to the targets
    if (accepted(app_id, spike)) {
        prov.n_spikes_forwarded += 1;
        uint32_t key = get_key();
        spin1_send_mc_packet(key, spike, WITH_PAYLOAD);
    }
}

void start_callback(void) {
    running = true;
    while (running) {
        // Get the next packet
        uint32_t cspr = spin1_irq_disable();
        while (running && circular_buffer_size(input_queue) == 0) {
            spin1_mode_restore(cspr);
            wait_for_interrupt();
            cspr = spin1_irq_disable();
        }
        spin1_mode_restore(cspr);

        // If we are still running, process the spike
        if (running) {
            process_spike();
        }
    }
}

void exit_callback(void) {
    running = false;
}

void store_provenance_data(void *prov_region_addr) {
    // Copy across the provenance data
    spin1_memcpy(prov_region_addr, &prov, sizeof(filter_provenance_t));
}

void receive_spike_callback(uint key, uint payload) {
    // Try to put the spike in the input queue
    prov.n_spikes_received += 1;
    if (!circular_buffer_push(input_queue, key)) {
        // Queue overflowed
        prov.n_times_queue_overflowed += 1;
    }
}

bool initialise() {
    data_specification_metadata_t *ds = data_specification_get_data_address();
    if (!data_specification_read_header(ds)) {
        log_error("Failed to read data specification header");
        return false;
    }

    // set up the simulation interface
    uint32_t n_steps;
    bool run_forever;
    uint32_t step;
    if (!simulation_steps_initialise(
            data_specification_get_region(FILTER_REGION_SYSTEM, ds),
            APPLICATION_NAME_HASH, &n_steps, &run_forever, &step, 0, -2)) {
        return false;
    }
    simulation_set_provenance_function(
            store_provenance_data,
            data_specification_get_region(FILTER_REGION_PROVENANCE, ds));

    // Read in the filter configuration
    filter_config_t *sdram_config = data_specification_get_region(
            FILTER_REGION_CONFIG, ds);
    uint32_t config_size = sizeof(filter_config_t)
            + sizeof(uint32_t) * sdram_config->n_targets;
    config = spin1_malloc(config_size);
    if (config == NULL) {
        log_error("Failed to allocate %u bytes for filter configuration",
                config_size);
        return false;
    }
    spin1_memcpy(config, sdram_config, config_size);

    // Set up the input queue
    input_queue = circular_buffer_initialize(config->input_queue_size);
    if (input_queue == NULL) {
        log_error("Failed to create input queue of size %u",
                config->input_queue_size);
        return false;
    }

    // Prepare the bitfield filters
    uint32_t n_entries = (config->app_id_max - config->app_id_min) + 1;
    filters = spin1_malloc(sizeof(bit_field_filter_info_t) * n_entries);
    if (filters == NULL) {
        log_error("Failed to allocate %u filters", n_entries);
        return false;
    }
    for (uint32_t i = 0; i < n_entries; i++) {
        filters[i].data = NULL;
    }

    // Read in the bit field filters
    filter_region_t *bitfield_region = data_specification_get_region(
            FILTER_REGION_BITFIELDS, ds);
    pop_table_config_t *master_pop_table_region = data_specification_get_region(
            FILTER_REGION_POP_TABLE, ds);
    filter_info_t *filters_sdram = bitfield_region->filters;
    for (uint32_t i = 0; i < bitfield_region->n_filters; i++) {
        uint32_t app_id = (filters_sdram[i].key & config->app_id_mask)
                >> config->app_id_shift;
        if ((app_id < config->app_id_min) || (app_id > config->app_id_max)) {
            log_error("Filter key 0x%08x has app id %u outside of range %u-%u",
                    filters_sdram[i].key, app_id, config->app_id_min,
                    config->app_id_max);
            return false;
        }

        uint32_t pos = app_id - config->app_id_min;
        filters[pos].mask = ~(master_pop_table_region->data[i].mask
                | (master_pop_table_region->data[i].core_mask
                        << master_pop_table_region->data[i].mask_shift));
        filters[pos].all_ones = filters_sdram[i].all_ones;
        filters[pos].n_colour_bits =
                master_pop_table_region->data[i].n_colour_bits;
        filters[pos].core_mask =
                master_pop_table_region->data[i].core_mask;
        filters[pos].core_shift =
                master_pop_table_region->data[i].mask_shift;
        filters[pos].n_neurons =
                master_pop_table_region->data[i].n_neurons;

        uint32_t size = get_bit_field_size(
                filters_sdram[i].n_atoms) * sizeof(uint32_t);
        filters[pos].data = spin1_malloc(size);
        if (filters[pos] == NULL) {
            log_error("Failed to allocate bit field of %u atoms for app id %u",
                    filters_sdram[i].n_atoms, app_id);
            return false;
        }
        spin1_memcpy(filters[pos].data, filters_sdram[i].data, size);
    }

    return true;
}

//! \brief The entry point for this model.
void c_main(void) {
    // initialise the model
    if (!initialize()) {
        rt_error(RTE_SWERR);
    }

    simulation_set_exit_function(exit_callback);
    simulation_set_start_function(start_callback);
    simulation_set_uses_timer(false);
    spin1_callback_on(MC_PACKET_RECEIVED, receive_spike_callback, -1);
    simulation_run();
}
