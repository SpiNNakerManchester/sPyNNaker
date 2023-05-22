/*
 * Copyright (c) 2021 The University of Manchester
 * based on work Copyright (c) The University of Sussex,
 * Garibaldi Pineda Garcia, James Turner, James Knight and Thomas Nowotny
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
//! \file DTCM-only convolutional processing implementation

#include "local_only_impl.h"
#include "local_only_2d_common.h"
#include <stdlib.h>
#include <debug.h>
#include "../population_table/population_table.h"
#include "../neuron.h"

typedef struct {
	//! The size of the source in the dimension
	uint32_t size_per_core;
	//! The values used to divide to get the dimension value from a scalar
	div_const size_per_core_div;
	//! The number of cores in the full population in this dimension
	uint32_t cores;
	//! Division by cores per dim
	div_const cores_div;
	//! The size of the last core in the dimension
	uint32_t size_last_core;
	//! The division by the dimension on the last core
	div_const size_last_core_div;
	//! The start position of the dimension that maps to this core
} source_dim;

typedef struct {
    key_info key_info;
    uint32_t n_dims;
    source_dim source_dim[];
} source_info;

// One per connector
typedef struct {
    uint16_t n_dims;
    uint16_t n_weights;
    uint16_t positive_synapse_type;
    uint16_t negative_synapse_type;
    uint16_t delay_stage;
    uint16_t delay;
    div_const pool_stride_div[];
    // Also follows:
    // lc_weight_t weights[];
} connector;

typedef struct {
    uint32_t n_post;
    uint32_t n_sources;
    uint32_t n_connectors;
    // In SDRAM, below here is the following (each variable size):
    // source_info sources[];
    // connector connectors[n_connectors]
} conv_config;

// The main configuration data
static conv_config *config;

// The source information
static source_info **source_infos;

// The per-connection data
static connector** connectors;

static inline lc_weight_t *get_weights(connector *conn) {
    return (lc_weight_t *) &conn->pool_stride_div[conn->n_dims];
}

//! \brief Load the required data into DTCM.
bool local_only_impl_initialise(void *address){
    log_info("+++++++++++++++++ CONV init ++++++++++++++++++++");
    conv_config* sdram_config = address;
    uint32_t config_size = sizeof(conv_config) +
    		(sizeof(source_info) * sdram_config->n_sources);
    config = spin1_malloc(config_size);
    if (config == NULL) {
    	log_error("Can't allocate %u bytes of memory for config with %u sources",
    			config_size, sdram_config->n_sources);
    	return false;
    }
    spin1_memcpy(config, sdram_config, config_size);

    log_info("num connectors = %u", config->n_connectors);
    if (config->n_connectors == 0) {
        return false;
    }

    log_info("num post = %u", config->n_post);

    // Allocate space for source information
    source_infos = spin1_malloc(config->n_sources * sizeof(source_infos[0]));
    if (source_infos == NULL) {
    	log_error("Can't allocate memory for source infos");
    }

    // Allocate space for connector information
    connectors = spin1_malloc(config->n_connectors * sizeof(connectors[0]));
    if (connectors == NULL) {
        log_error("Can't allocate memory for connectors");
        return false;
    }

    // The first source comes after the configuration in SDRAM
    source_info *s_info = (source_info *) &sdram_config[1];
    for (uint32_t i = 0; i < config->n_sources; i++) {
    	uint32_t n_bytes = sizeof(*s_info) + (s_info->n_dims * sizeof(source_dim));
    	source_infos[i] = spin1_malloc(n_bytes);
    	if (source_infos[i] == NULL) {
    		log_error("Can't allocate %u bytes for source_infos[%u]", n_bytes, i);
    	}
    	spin1_memcpy(source_infos[i], s_info, n_bytes);

    	// Move to the next source, after the last dimension
    	s_info = (source_info *) &s_info->source_dim[source_infos[i]->n_dims];
    }

    // The first connector comes after the sources in SDRAM
    connector *conn = (connector *) s_info;
    for (uint32_t i = 0; i < config->n_connectors; i++) {

        uint32_t n_bytes = sizeof(*conn) + (conn->n_weights * sizeof(lc_weight_t)) +
                (conn->n_dims * sizeof(div_const));

        // Copy the data from SDRAM
        connectors[i] = spin1_malloc(n_bytes);
        if (connectors[i] == NULL) {
            log_error("Can't allocate %u bytes for connectors[%u]", n_bytes, i);
            return false;
        }
        spin1_memcpy(connectors[i], conn, n_bytes);

        // Move to the next connector; because it is dynamically sized,
        // this comes after the last weight in the last connector, which comes
        // after the last dimension!
        lc_weight_t* weights = get_weights(conn);
        uint32_t n_weights = connectors[i]->n_weights;
        if (n_weights & 0x1) {
        	n_weights += 1;
        }
        conn = (connector *) &weights[n_weights];
    }

    return true;
}

static inline bool key_to_index_lookup(uint32_t spike, source_info **rs_info) {
    for (uint32_t i = 0; i < config->n_sources; i++) {
        source_info *s_info = source_infos[i];
        if ((spike & s_info->key_info.mask) == s_info->key_info.key) {
        	*rs_info = s_info;
			return true;
        }
    }
    return false;
}

static bool get_conn_weights(connector *c, source_info *s_info, uint32_t local_id,
		uint32_t *sizes, uint32_t *core_coords, div_const *divs,
		uint32_t neurons_per_core, lc_weight_t **weights) {

	// Stop if the delay means it is out of range
	uint32_t first_neuron = c->delay_stage * neurons_per_core;
	uint32_t last_neuron = first_neuron + neurons_per_core;
	if (local_id < first_neuron || local_id >= last_neuron) {
		return false;
	}
	local_id -= first_neuron;

	// Now work out the index into the weights from the coordinates
	uint32_t last_extent = 1;
	uint32_t index = 0;
    uint32_t remainder = local_id;
	for (uint32_t j = 0; j < s_info->n_dims; j++) {
		div_const stride_div = c->pool_stride_div[j];
		source_dim *s_dim = &s_info->source_dim[j];

		uint32_t coord = div_by_const(remainder, divs[j]);
		remainder -= coord * sizes[j];
		coord += core_coords[j] * s_dim->size_per_core;

		// Work out the position after pooling
		coord = div_by_const(coord, stride_div);

		// Add into the final index
		index += (coord * last_extent);

		// Remember the shape from this dimension to pass to the next
		last_extent = sizes[j];
	}
	lc_weight_t *all_weights = get_weights(c);
	*weights = &all_weights[index * config->n_post];
	return true;
}

//! \brief Process incoming spikes. In this implementation we need to:
//! 1. Check if it's in the population table
//! 2. Convert the relative (per core) Id to a global (per population) one
//! 3. Obtain the post-ids and weights which will be reached by the spike/kernel
//!    combination.
//! 4. Add the weights to the appropriate current buffers
void local_only_impl_process_spike(
        uint32_t time, uint32_t spike, uint16_t* ring_buffers) {

    // Lookup the spike, and if found, get the appropriate parts
    source_info *s_info;
    if (!key_to_index_lookup(spike, &s_info)) {
        return;
    }

	// Work out the local coordinate for this source
    uint32_t core_id = get_core_id(spike, s_info->key_info);
    uint32_t local_id = get_local_id(spike, s_info->key_info);
	uint32_t sizes[s_info->n_dims];
	uint32_t core_coords[s_info->n_dims];
	div_const divs[s_info->n_dims];
	uint32_t neurons_per_core = 1;
	uint32_t core_remainder = core_id;
	for (uint32_t j = 0; j < s_info->n_dims; j++) {
		source_dim *s_dim = &s_info->source_dim[j];
		// Get the core coordinates for this dimension in the global space
		core_coords[j] = div_by_const(core_remainder, s_dim->cores_div);
		bool is_last_core = core_coords[j] == (s_dim->cores - 1);
		core_remainder -= core_coords[j] * s_dim->cores;
		if (is_last_core) {
			sizes[j] = s_dim->size_last_core;
			divs[j] = s_dim->size_last_core_div;
		} else {
			sizes[j] = s_dim->size_per_core;
			divs[j] = s_dim->size_per_core_div;
		}
		neurons_per_core *= sizes[j];
    }

    // Go through the weights and process them into the ring buffers
    uint32_t end = s_info->key_info.start + s_info->key_info.count;
    for (uint32_t i = s_info->key_info.start; i < end; i++) {
	    connector *connector = connectors[i];
	    lc_weight_t *weights;
	    if (!get_conn_weights(connector, s_info, local_id, sizes, core_coords,
	    		divs, neurons_per_core, &weights)) {
	    	continue;
	    }

		for (uint32_t post_index = 0; post_index < config->n_post; post_index++) {

			lc_weight_t weight = weights[post_index];
			if (weight == 0) {
				continue;
			}
			uint32_t rb_index = 0;
			if (weight > 0) {
				rb_index = synapse_row_get_ring_buffer_index(time + connector->delay,
					connector->positive_synapse_type, post_index,
					synapse_type_index_bits, synapse_index_bits,
					synapse_delay_mask);
			} else {
				rb_index = synapse_row_get_ring_buffer_index(time + connector->delay,
					connector->negative_synapse_type, post_index,
					synapse_type_index_bits, synapse_index_bits,
					synapse_delay_mask);
				weight = -weight;
			}
			log_debug("Updating ring_buffers[%u] for post neuron %u with weight %u",
					rb_index, post_index, weight);

			// Add weight to current ring buffer value, avoiding saturation
			uint32_t accumulation = ring_buffers[rb_index] + weight;
			uint32_t sat_test = accumulation & 0x10000;
			if (sat_test) {
				accumulation = sat_test - 1;
			}
			ring_buffers[rb_index] = accumulation;
		}
    }
}
