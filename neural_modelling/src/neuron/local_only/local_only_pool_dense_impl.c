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
#include <stdlib.h>
#include <debug.h>
#include "../population_table/population_table.h"
#include "../neuron.h"

typedef int16_t lc_weight_t;

// Dimensions are needed to be signed due to mapping from pre- to post-synaptic.
typedef int16_t lc_dim_t;

// Reduce the number of parameters with the following structs
typedef struct {
    lc_dim_t row;
    lc_dim_t col;
} lc_coord_t;

typedef struct {
    lc_dim_t height;
    lc_dim_t width;
} lc_shape_t;

typedef struct {
    uint32_t key;
    uint32_t mask;
    //! The index into ::connectors for this entry
	uint32_t start: 13;
	//! The number of bits of key used for colour (0 if no colour)
	uint32_t n_colour_bits: 3;
	//! The number of entries in ::connectors for this entry
	uint32_t count: 16;
	//! The mask to apply to the key once shifted to get the core index
	uint32_t core_mask: 16;
	//! The shift to apply to the key to get the core part
	uint32_t mask_shift: 16;
	//! The number of neurons per core
	uint32_t n_neurons: 16;
} source_info;

// A reciprocal of a 16-bit signed integer will have 1 sign bit, 1 integer bit
// and 14 fractional bits to allow 1 to be properly represented
#define RECIP_FRACT_BITS 14

// Information about each dimension
typedef struct {
	//! The size of the source in the dimension
    uint32_t dim_size;
    //! The values used to divide to get the dimension value from a scalar
    uint32_t dim_m;
    uint32_t dim_sh1: 16;
    uint32_t dim_sh2: 16;
    //! The start position of the dimension that maps to this core
    uint16_t pre_in_post_start;
    uint16_t pre_in_post_end;
    uint16_t pre_in_post_shape;
    uint16_t recip_pool_stride;
} dimension;

// One per connector
typedef struct {
    uint32_t n_dims;
    uint32_t n_weights;
    uint16_t positive_synapse_type;
    uint16_t negative_synapse_type;
    uint32_t delay;
    dimension dimensions[];
    // Also follows:
    // lc_weight_t weights[];
} connector;

typedef struct {
    uint32_t n_post;
    uint32_t n_sources;
    uint32_t n_connectors;
    source_info sources[];
    // In SDRAM, below here is the following (each variable size):
    // connector connectors[n_connectors]
} conv_config;

// The main configuration data
static conv_config *config;

// The per-connection data
static connector** connectors;

static lc_weight_t *get_weights(connector *conn) {
    return (lc_weight_t *) &conn->dimensions[conn->n_dims];
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

    // Allocate space for connector information and pre-to-post table
    connectors = spin1_malloc(config->n_connectors * sizeof(connectors[0]));
    if (connectors == NULL) {
        log_error("Can't allocate memory for connectors");
        return false;
    }

    // The first connector comes after the configuration in SDRAM
    connector *conn = (connector *) &sdram_config[1];
    for (uint32_t i = 0; i < config->n_connectors; i++) {

        uint32_t n_bytes = sizeof(*conn) + (conn->n_weights * sizeof(lc_weight_t)) +
                (conn->n_dims * sizeof(dimension));

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

//! \brief Multiply an integer by a 16-bit reciprocal and return the floored
//!        integer result
static inline int16_t recip_multiply(int16_t integer, int16_t recip) {
    int32_t i = integer;
    int32_t r = recip;
    return (int16_t) ((i * r) >> RECIP_FRACT_BITS);
}

static inline uint32_t get_pop_neuron_id(uint32_t spike, source_info *s_info) {
	uint32_t local_mask = ~s_info->mask | (s_info->core_mask << s_info->mask_shift);
	uint32_t local = spike & local_mask;
	uint32_t core_id = ((spike >> s_info->mask_shift) & s_info->core_mask);
	uint32_t core_sum = core_id * s_info->n_neurons;
	return (local >> s_info->n_colour_bits) + core_sum;
}

static inline uint32_t div_by_dim_size(uint32_t n, dimension *dim) {
	uint32_t t1 = (uint32_t) (((uint64_t) n * (uint64_t) dim->dim_m) >> 32);
	uint32_t nsubt1 = (n - t1) >> dim->dim_sh1;
	return (t1 + nsubt1) >> dim->dim_sh2;
}

static inline bool key_to_index_lookup(uint32_t spike, uint32_t *start,
		uint32_t *end, uint32_t *pop_neuron_id) {
    for (uint32_t i = 0; i < config->n_sources; i++) {
        source_info *s_info = &(config->sources[i]);
        if ((spike & s_info->mask) == s_info->key) {
        	*start = s_info->start;
        	*end = s_info->start + s_info->count;
        	// Get the population-based neuron id
			*pop_neuron_id = get_pop_neuron_id(spike, s_info);
			return true;
        }
    }
    return false;
}

bool get_conn_weights(uint32_t pop_neuron_id, uint32_t i, lc_weight_t **weights) {
	connector *c = connectors[i];

	// Now work out the index into the weights from the coordinates
	uint32_t last_extent = 1;
	uint32_t index = 0;
    uint32_t remainder = pop_neuron_id;
	for (uint32_t j = 0; j < c->n_dims; j++) {
		dimension *dim = &c->dimensions[j];

		// Get the coordinate for this dimension in the global space
		uint32_t coord = div_by_dim_size(remainder, dim);

		// Work out the position after pooling
		coord = recip_multiply(coord, dim->recip_pool_stride);

		// Check that the coordinate is in range now for this core
		if (coord < dim->pre_in_post_start || coord > dim->pre_in_post_end) {
			return false;
		}

		// Get the local coordinate after pooling and add into the
		// final index
		coord -= dim->pre_in_post_start;
		index += (coord * last_extent);

		// Remember the shape from this dimension to pass to the next
		last_extent = dim->pre_in_post_shape;
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
    uint32_t start;
    uint32_t end;
    uint32_t pop_neuron_id;
    if (!key_to_index_lookup(spike, &start, &end, &pop_neuron_id)) {
        return;
    }

    // Go through the weights and process them into the ring buffers
    for (uint32_t i = start; i < end; i++) {
	    connector *connector = connectors[i];
	    lc_weight_t *weights;
	    if (!get_conn_weights(pop_neuron_id, i, &weights)) {
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
