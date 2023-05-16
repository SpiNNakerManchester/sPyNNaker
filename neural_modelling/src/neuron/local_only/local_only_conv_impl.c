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
#include <stdfix-full-iso.h>
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

// A reciprocal of a 16-bit signed integer will have 1 sign bit, 1 integer bit
// and 14 fractional bits to allow 1 to be properly represented
#define RECIP_FRACT_BITS 14

// One per connector
typedef struct {
	//! The shape of the kernel
    lc_shape_t kernel;
    //! The shape of the padding
    lc_shape_t padding;
    //! 1 / shape of stride
    lc_coord_t recip_strides;
    //! 1 / shape of pooling stride
    lc_coord_t recip_pool_strides;
    //! The index of the synapse for positive weights
    uint16_t positive_synapse_type;
    //! The index of the synapse for negative weights
    uint16_t negative_synapse_type;
	//! The first source neuron to accept (helps with delay extensions)
	uint16_t first_neuron;
    //! The last source neuron to accept (helps with delay extensions)
	uint16_t last_neuron;
	//! The delay in time steps
    uint16_t delay;
    //! The index of the weights for the kernel
    uint16_t kernel_index;
} connector;

typedef struct {

} reciprocal;

typedef struct {
	//! The key to match against the incoming message
	uint32_t key;
	//! The mask to select the relevant bits of \p key for matching
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
	//! The source population height per core
	uint32_t source_height_per_core: 16;
	//! The source population width per core
	uint32_t source_width_per_core: 16;
	//! Used to calculate division by the source width per core efficiently
    uint32_t source_width_m: 16;
    uint32_t source_width_sh1: 8;
    uint32_t source_width_sh2: 8;
    //! Number of cores in a width
    uint32_t cores_per_source_width;
    //! Division by cores per source width
    uint32_t cores_per_source_m: 16;
    uint32_t
} source_info;

typedef struct {
    lc_coord_t post_start;
    lc_coord_t post_end;
    lc_shape_t post_shape;
    uint32_t n_sources;
    uint32_t n_connectors_total;
    uint32_t n_weights_total;
    source_info sources[];
    // In SDRAM, after sources[n_sources] is the following:
    // connector connectors[n_connectors_total];
    // lc_weight_t[n_weights_total] weights;
} conv_config;

// The main configuration data
static conv_config *config;

static connector *connectors;

static lc_weight_t *weights;

//! \brief Load the required data into DTCM.
bool local_only_impl_initialise(void *address){
    log_info("+++++++++++++++++ CONV init ++++++++++++++++++++");
    conv_config* sdram_config = address;
    uint32_t n_bytes = sizeof(conv_config) +
    		(sizeof(source_info) * sdram_config->n_sources);
    config = spin1_malloc(n_bytes);
    if (config == NULL) {
    	log_error("Can't allocate memory for config!");
    	return false;
    }
    spin1_memcpy(config, sdram_config, n_bytes);

    log_info("post_start = %u, %u, post_end = %u, %u, post_shape = %u, %u",
            config->post_start.col, config->post_start.row,
            config->post_end.col, config->post_end.row,
            config->post_shape.width, config->post_shape.height);
    log_info("num sources = %u", config->n_sources);

    if (config->n_sources == 0) {
    	log_error("No sources!");
    	return false;
    }

    // The connectors come after the sources in SDRAM
    connector *sdram_connectors =
    		(connector *) &(sdram_config->sources[config->n_sources]);
    uint32_t n_connector_bytes = sizeof(connector) * config->n_connectors_total;
    connectors = spin1_malloc(n_connector_bytes);
    if (connectors == NULL) {
    	log_error("Can't allocate %u bytes of memory for %u connectors!",
    			n_connector_bytes, config->n_connectors_total);
    	return false;
    }

    // The weights come after the connectors in SDRAM
    lc_weight_t *kernel_weights =
    		(lc_weight_t *) &(sdram_connectors[config->n_connectors_total]);
    uint32_t n_weight_bytes = sizeof(lc_weight_t) * config->n_weights_total;
    weights = spin1_malloc(n_weight_bytes);
    if (weights == NULL) {
    	log_error("Can't allocate %u bytes of memory for %u weights!",
    			n_weight_bytes, config->n_weights_total);
    	return false;
    }
    spin1_memcpy(weights, kernel_weights, n_weight_bytes);

    // Print what we have
    for (uint32_t i = 0; i < config->n_sources; i++) {
        log_info("Source %u: key=0x%08x, mask=0x%08x",
                i, config->sources[i].key, config->sources[i].mask);
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

//! \brief Do a mapping from pre to post 2D spaces, we use the standard
//! padding, kernel, strides from Convolutional Neural Networks
//! because of the way we're looping through the kernel, we divide the kernel
//! shape by 2.
static inline lc_coord_t map_pre_to_post(connector *connector, lc_coord_t pre,
        int16_t half_kh, int16_t half_kw) {
    lc_coord_t post = pre;
    post.col = recip_multiply(post.col, connector->recip_pool_strides.col);
    post.row = recip_multiply(post.row, connector->recip_pool_strides.row);
    post.col = post.col - half_kw + connector->padding.width;
    post.row = post.row - half_kh + connector->padding.height;
    post.col = recip_multiply(post.col, connector->recip_strides.col);
    post.row = recip_multiply(post.row, connector->recip_strides.row);
    return post;
}


//! \brief Given a pre-synaptic coordinate we obtain which post-synaptic
//!        coordinates will be affected (i.e. which of them are 'reached' by
//!        the kernel).
static inline void do_convolution_operation(
        uint32_t time, lc_coord_t pre_coord, connector *connector,
        uint16_t *ring_buffers) {
    int32_t half_kh = connector->kernel.height / 2;
    int32_t half_kw = connector->kernel.width / 2;
    lc_coord_t post_coord = map_pre_to_post(connector, pre_coord, half_kh, half_kw);
    log_debug("pre row %d, col %d AS post row %d, col %d",
            pre_coord.row, pre_coord.col, post_coord.row, post_coord.col);
    lc_weight_t *connector_weights = &weights[connector->kernel_index];

    int32_t kw = connector->kernel.width;
    for (int32_t r = -half_kh, kr = 0; r <= half_kh; r++, kr++) {
        int32_t tmp_row = post_coord.row + r;
        if ((tmp_row < config->post_start.row) || (tmp_row > config->post_end.row)) {
            continue;
        }
        for (int32_t c = -half_kw, kc = 0; c <= half_kw; c++, kc++) {
            int32_t tmp_col = post_coord.col + c;
            if ((tmp_col < config->post_start.col) || (tmp_col > config->post_end.col)) {
                continue;
            }

            // This the neuron id relative to the neurons on this core
            uint32_t post_index =
                ((tmp_row - config->post_start.row) * config->post_shape.width)
                    + (tmp_col - config->post_start.col);
            uint32_t k = (kr * kw) + kc;
            lc_weight_t weight = connector_weights[k];
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
            log_debug("Updating ring_buffers[%u] for post neuron %u = %u, %u, with weight %u",
                    rb_index, post_index, tmp_col, tmp_row, weight);

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

static inline uint32_t get_core_id(uint32_t spike, source_info *s_info) {
	return ((spike >> s_info->mask_shift) & s_info->core_mask);
}

static inline uint32_t get_core_row(uint32_t core_id, source_info *s_info) {
	return core_id * s_info->source_width;
}

static inline uint32_t get_local_id(uint32_t spike, source_info *s_info) {
	uint32_t local_mask = ~s_info->mask | (s_info->core_mask << s_info->mask_shift);
    uint32_t local = spike & local_mask;
    return local >> s_info->n_colour_bits;
}

static inline uint32_t div_by_width(uint32_t n, source_info *s_info) {
	uint32_t t1 = (n * s_info->source_width_m) >> 16;
	uint32_t nsubt1 = (n - t1) >> s_info->source_width_sh1;
	return (t1 + nsubt1) >> s_info->source_width_sh2;
}

static inline bool key_to_index_lookup(uint32_t spike, uint32_t *start_index,
		uint32_t *end_index, uint32_t *local_id, source_info **rs_info) {
    for (uint32_t i = 0; i < config->n_sources; i++) {
        source_info *s_info = &(config->sources[i]);
        // We have a match on key
        if ((spike & s_info->mask) == s_info->key) {
        	*rs_info = s_info;
        	// Use the info in the source to note where to start and end
        	*start_index = s_info->start;
        	*end_index = s_info->start + s_info->count;
        	// Get the population-based neuron id
        	*pop_neuron_id = get_pop_neuron_id(spike, s_info);
        	return true;
        }
    }
    return false;
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
    source_info *s_info;
    if (!key_to_index_lookup(spike, &start, &end, &pop_neuron_id, &s_info)) {
    	log_warning("Spike %u didn't match any connectors!", spike);
        return;
    }
    log_debug("Received spike %u using connectors between %u and %u",
    		spike, start, end);

    // compute the population-based coordinates
    for (uint32_t i = start; i < end; i++) {
		connector *connector = &(connectors[i]);

    	// We are ignoring the neuron because the delay does not match
    	if (pop_neuron_id < connector->first_neuron
    			|| pop_neuron_id > connector->last_neuron) {
    		continue;
    	}

    	uint32_t local_pop_neuron_id = pop_neuron_id - connector->first_neuron;

    	// Calculate the source x and y by dividing by source width
    	uint32_t y = div_by_width(local_pop_neuron_id, s_info);

    	lc_coord_t pre_coord = {
    	    // The x-coordinate is the remainder of the "division"
    	    .col = pop_neuron_id - (y * s_info->source_width),
    	    // The y-coordinate is the integer part of the "division".
    	    .row = y
    	};

		// Compute the convolution
		do_convolution_operation(time, pre_coord, connector, ring_buffers);
    }
}
