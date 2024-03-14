/*
 * Copyright (c) 2014 The University of Manchester
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

/*!
 * \dir
 * \brief Implementation of the Poisson spike source
 * \file
 * \brief This file contains the main functions for a Poisson spike generator.
 */

#include <common/maths-util.h>
#include <common/send_mc.h>
#include <data_specification.h>
#include <recording.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>
#include <circular_buffer.h>

#ifndef UNUSED
#define UNUSED __attribute__((__unused__))
#endif

#define MAX_PACKETS 1024

enum REGIONS {
	SYSTEM, CONFIG, KEYS, RECORDING, PROVENANCE
};

typedef struct key_entry {
	// The key to match
    uint32_t key;
    // The mask to apply to the key to get a match
    uint32_t mask;
    // The number of bits used for the colour
    uint32_t n_colour_bits;
    // The minimum neuron id of the source core
    uint32_t min_neuron_id;
    // The index of the position in the journey
    uint32_t node_index;
    // The number of neurons for each value of the position
    uint32_t neurons_per_value;
} key_entry;

typedef struct source_value {
	uint32_t last_spike_time;

	// We are currently in a run of spikes for this value, currently this long
	uint32_t run_length;
} source_value;

typedef struct config {

	// Whether to send data
	uint32_t send_results;

	// The key to send results with
	uint32_t results_key;

	// Whether to send Poisson control
	uint32_t send_poisson_control;

	// The key to send Poisson control with
	uint32_t poisson_control_key;

	// The minimum run length to consider this a useful value
	uint32_t min_run_length;

	// The maximum distance between spikes to consider them part of the same run
	uint32_t max_spike_diff;

	// The number of sources
	uint32_t n_sources;

	// The number of values of each source
	uint32_t n_values;

	// The number of key entries
	uint32_t n_key_entries;

} config;

typedef struct recording {
	uint32_t time;
	uint32_t values[];
} recording;

static uint32_t time;

static uint32_t simulation_ticks;

static uint32_t infinite_run;

static uint32_t timer_period;

static config cfg;

static key_entry *key_entries;

static source_value **source_values;

static uint32_t *n_source_values_active;

static circular_buffer packets;

static uint32_t recording_flags;

static recording *rec;

static uint32_t rec_size;

static inline uint32_t div(uint32_t a, uint32_t b) {
	uint32_t rem = a;
	uint32_t count = 0;
	while (rem >= b) {
		rem -= b;
		count++;
	}
	return count;
}

static inline uint32_t check_runs(void) {
	uint32_t source[cfg.n_values];

	for (uint32_t i = 0; i < cfg.n_sources; i++) {
		rec->values[i] = cfg.n_values;
	}
	for (uint32_t i = 0; i < cfg.n_values; i++) {
		source[i] = cfg.n_sources;
	}

	for (uint32_t i = 0; i < cfg.n_sources; i++) {

		// If this source is not single valued, return
		if (n_source_values_active[i] != 1) {
			return 0;
		}

		// Find the single value of this source
		for (uint32_t j = 0; j < cfg.n_values; j++) {
			if (source_values[i][j].run_length >= cfg.min_run_length) {

				// If already found a value, fail
				if (rec->values[i] != cfg.n_values) {
					log_debug("Value %d already found for source %d", rec->values[i], i);
					return 0;
				}

				// If the value has already been used, fail
				if (source[j] != cfg.n_sources) {
					log_debug("Value %d already used", j);
					return 0;
				}

				// Store the value of the source and the source for the value
				log_debug("Source %d has value %d", i, j);
				rec->values[i] = j;
				source[j] = i;
				break;
			}
		}

		// If not found, fail!
		if (rec->values[i] == cfg.n_values) {
			return 0;
		}
	}

	// We got through so we should have a unique value for every source
	return 1;
}

static inline void send_results(void) {
	if (!cfg.send_results) {
		return;
	}
	for (uint32_t i = 0; i < cfg.n_sources; i++) {
		send_spike_mc_payload(cfg.results_key + i, rec->values[i]);
	}
}

static inline void record(void) {
	rec->time = time;
	recording_record(0, rec, rec_size);
}

static void resume_callback(void) {
	recording_reset();
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!     executed since start of simulation
//! \param[in] unused: for consistency sake of the API always returning two
//!     parameters, this parameter has no semantics currently and thus
//!     is set to 0
static void timer_callback(UNUSED uint timer_count, UNUSED uint unused) {
	time++;
	if (simulation_is_finished()) {
		log_info("Simulation complete");

		simulation_handle_pause_resume(resume_callback);

		if (recording_flags) {
		    recording_finalise();
		}

		simulation_ready_to_read();
		return;
	}

	uint32_t item;
	uint32_t source_check_required = 0;

	// Go through the buffer of keys
	while (circular_buffer_get_next(packets, &item)) {

		// Find the entry for this key
		key_entry *entry = NULL;
		for (uint32_t i = 0; i < cfg.n_key_entries; i++) {
			if ((item & key_entries[i].mask) == key_entries[i].key) {
				entry = &key_entries[i];
				break;
			}
		}

		// Skip if the entry is not found
		if (entry == NULL) {
			log_error("Received unexpected key %08x", item);
			continue;
		}

		// Find the source value for the key
		uint32_t index = ((item & ~entry->mask) >> entry->n_colour_bits) - entry->min_neuron_id;
		uint32_t value = div(index, entry->neurons_per_value);
		source_value *source_value = &source_values[entry->node_index][value];

		log_debug("Time %u, last %u, received key %08x, index %d, value %d, node %d,"
				" run_length %d",
				time, source_value->last_spike_time, item, index, value, entry->node_index,
				source_value->run_length);

		if ((time - source_value->last_spike_time) > cfg.max_spike_diff) {
			// The source spike is too late compared to the last, so no longer a run

			// If it was a run, reset
			if (source_value->run_length >= cfg.min_run_length) {
				// The run is now too short to be considered important
				n_source_values_active[entry->node_index]--;
				log_debug("n_source_values_active[%d] = %d", entry->node_index,
						n_source_values_active[entry->node_index]);
				// If this means there is now only one run active, we need to check
				if (n_source_values_active[entry->node_index] == 1) {
					source_check_required = 1;
				}
			}
			source_value->run_length = 0;

		} else {
			// The source spike is part of a run
			source_value->run_length++;

			if (source_value->run_length == cfg.min_run_length) {
				// The run is now long enough to be considered important
				n_source_values_active[entry->node_index]++;
				log_debug("n_source_values_active[%d] = %d", entry->node_index,
					    n_source_values_active[entry->node_index]);

				// If this means there is now only one run active, we need to check
				if (n_source_values_active[entry->node_index] == 1) {
					source_check_required = 1;
				}
			}
		}
		source_value->last_spike_time = time;
	}

	// Go through each source value and check if it should be in-active now
	for (uint32_t i = 0; i < cfg.n_sources; i++) {
		for (uint32_t j = 0; j < cfg.n_values; j++) {
			if ((time - source_values[i][j].last_spike_time) > cfg.max_spike_diff) {
				if (source_values[i][j].run_length >= cfg.min_run_length) {
					n_source_values_active[i]--;
					log_debug("n_source_values_active[%d] = %d", i,
							n_source_values_active[i]);
					if (n_source_values_active[i] == 1) {
						source_check_required = 1;
					}
				}
				source_values[i][j].run_length = 0;
			}
		}
	}

	// If something significant has happened, check the runs
	if (source_check_required) {
		log_debug("Checking runs");
		if (check_runs()) {
			send_results();
			record();
		}
	}
}

//! \brief Multicast callback used to set rate when injected in a live example
//! \param[in] key: Received multicast key
//! \param[in] payload: Received multicast payload
static void multicast_packet_callback(uint key, UNUSED uint unused) {
    circular_buffer_add(packets, key);
}

static void store_provenance(uint32_t *prov_items) {
	prov_items[0] = circular_buffer_get_n_buffer_overflows(packets);
}

static uint32_t initialize(void) {
	// Get the address this core's DTCM data starts at from SRAM
	data_specification_metadata_t *ds_regions =
			data_specification_get_data_address();

	// Read the header
	if (!data_specification_read_header(ds_regions)) {
		return 0;
	}

	// Get the timing details and set up the simulation interface
	log_debug("Setting up simulation interface");
	if (!simulation_initialise(
			data_specification_get_region(SYSTEM, ds_regions),
			APPLICATION_NAME_HASH, &timer_period, &simulation_ticks,
			&infinite_run, &time, 1, 1)) {
		return 0;
	}

	simulation_set_provenance_function(
	        store_provenance,
	        data_specification_get_region(PROVENANCE, ds_regions));

	// Get the configuration details
	log_debug("Copying Configuration");
	config *sdram_config = data_specification_get_region(CONFIG, ds_regions);
	cfg = *sdram_config;
	log_info("Config: send=%d, key=%08x, min_run_length=%d, max_spike_diff=%d,"
			" n_sources=%d, n_values=%d, n_key_entries=%d",
			cfg.send_results, cfg.results_key, cfg.min_run_length, cfg.max_spike_diff,
			cfg.n_sources, cfg.n_values, cfg.n_key_entries);

	// Set up the key entries
	key_entry *key_entries_sdram =
			(key_entry *) data_specification_get_region(KEYS, ds_regions);
	key_entries = spin1_malloc(cfg.n_key_entries * sizeof(key_entry));
	if (key_entries == NULL) {
		log_error("Could not allocate memory for key entries");
		return 0;
	}
	log_debug("Copying keys");
    spin1_memcpy(key_entries, key_entries_sdram, cfg.n_key_entries * sizeof(key_entry));

    // Set up recording
    log_debug("Setting up recording");
    void *recording_data_address = data_specification_get_region(RECORDING, ds_regions);
    if (!recording_initialize(&recording_data_address, &recording_flags)) {
    	return 0;
    }
    log_debug("Recording flags = %08x", recording_flags);

	// Set up recording structure
	rec_size = sizeof(recording) + (cfg.n_sources * sizeof(uint32_t));
	rec = spin1_malloc(rec_size);
	if (rec == NULL) {
		log_error("Could not allocate memory for recording");
		return 0;
	}

    // Set up the source values
	log_debug("Setting up source values");
    source_values = spin1_malloc(cfg.n_sources * sizeof(source_value *));
	if (source_values == NULL) {
		log_error("Could not allocate memory for source values");
		return 0;
	}
	for (uint32_t i = 0; i < cfg.n_sources; i++) {
		source_values[i] = spin1_malloc(cfg.n_values * sizeof(source_value));
		if (source_values[i] == NULL) {
			log_error("Could not allocate memory for source value %d", i);
			return 0;
		}
		for (uint32_t j = 0; j < cfg.n_values; j++) {
			source_values[i][j].last_spike_time = 0;
			source_values[i][j].run_length = 0;
		}
	}

	// Set up the number of active source values
	log_debug("Setting up number of active source values");
	n_source_values_active = spin1_malloc(cfg.n_sources * sizeof(uint32_t));
	if (n_source_values_active == NULL) {
		log_error("Could not allocate memory for n source values active");
		return 0;
	}
	for (uint32_t i = 0; i < cfg.n_sources; i++) {
		n_source_values_active[i] = 0;
	}

	// Set up the buffer of packets
	log_debug("Setting up packet buffer");
	packets = circular_buffer_initialize(MAX_PACKETS);
	if (packets == NULL) {
		log_error("Could not allocate memory for packet buffer");
		return 0;
	}

	return 1;
}

//! The entry point for this model
void c_main(void) {
    // Load DTCM data
    time = 0;
    if (!initialize()) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Set timer tick (in microseconds)
    log_debug("Setting timer tick to %d microseconds", timer_period);
    spin1_set_timer_tick(timer_period);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, 1);
    spin1_callback_on(MC_PACKET_RECEIVED, multicast_packet_callback, -1);

    simulation_run();
}
