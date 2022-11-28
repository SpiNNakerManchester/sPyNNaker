/*
 * Copyright (c) The University of Sussex, Garibaldi Pineda Garcia,
 * James Turner, James Knight and Thomas Nowotny
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
    uint32_t n_colour_bits;
} source_key_info;

// A reciprocal of a 16-bit signed integer will have 1 sign bit, 1 integer bit
// and 14 fractional bits to allow 1 to be properly represented
#define RECIP_FRACT_BITS 14

// Information about each dimension
typedef struct {
    uint32_t mask;
    uint32_t shift;
    uint16_t pre_start;
    uint16_t pre_in_post_start;
    uint16_t pre_in_post_end;
    uint16_t pre_in_post_shape;
    uint16_t recip_pool_stride;
    uint16_t _PADDING;
} dimension;

// One per connector
typedef struct {
    source_key_info key_info;
    uint32_t n_dims;
    uint32_t n_weights;
    uint16_t positive_synapse_type;
    uint16_t negative_synapse_type;
    dimension dimensions[];
    // Also follows:
    // lc_weight_t weights[];
} connector;

typedef struct {
    uint32_t n_post;
    uint32_t n_connectors;
    // In SDRAM, below here is the following:
    // connector connectors[n_connectors]
} conv_config;

// The main configuration data
static conv_config config;

// The per-connection data
static connector** connectors;

static lc_weight_t *get_weights(connector *conn) {
    return (lc_weight_t *) &conn->dimensions[conn->n_dims];
}

//! \brief Load the required data into DTCM.
bool local_only_impl_initialise(void *address){
    log_info("+++++++++++++++++ CONV init ++++++++++++++++++++");
    conv_config* sdram_config = address;
    config = *sdram_config;

    log_info("num connectors = %u", config.n_connectors);
    if (config.n_connectors == 0) {
        return false;
    }

    log_info("num post = %u", config.n_post);

    // Allocate space for connector information and pre-to-post table
    connectors = spin1_malloc(config.n_connectors * sizeof(connectors[0]));
    if (connectors == NULL) {
        log_error("Can't allocate memory for connectors");
        return false;
    }

    // The first connector comes after the configuration in SDRAM
    connector *conn = (connector *) &sdram_config[1];
    for (uint32_t i = 0; i < config.n_connectors; i++) {
        log_info("Connector %u: key=0x%08x, mask=0x%08x",
                i, conn->key_info.key, conn->key_info.mask);

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
        conn = (connector *) &weights[connectors[i]->n_weights];
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

static inline bool key_to_index_lookup(uint32_t spike, connector **conn,
        lc_weight_t **weights) {
    for (uint32_t i = 0; i < config.n_connectors; i++) {
        connector *c = connectors[i];
        if ((spike & c->key_info.mask) == c->key_info.key) {
        	uint32_t local_spike = (spike & ~c->key_info.mask) >> c->key_info.n_colour_bits;
            *conn = c;

            // Now work out the index into the weights from the coordinates
            uint32_t last_extent = 1;
            uint32_t index = 0;
            for (uint32_t j = 0; j < c->n_dims; j++) {
                dimension *dim = &c->dimensions[j];

                // Get the coordinate for this dimension from the spike
                uint32_t coord = (local_spike & dim->mask) >> dim->shift;

                // Work out the position in the global space
                coord += dim->pre_start;

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
            *weights = &all_weights[index * config.n_post];
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
    connector *connector;
    lc_weight_t *weights;

    // Lookup the spike, and if found, get the appropriate parts
    if (!key_to_index_lookup(spike, &connector, &weights)) {
        return;
    }

    // Go through the weights and process them into the ring buffers
    for (uint32_t post_index = 0; post_index < config.n_post; post_index++) {
        lc_weight_t weight = weights[post_index];
        if (weight == 0) {
            continue;
        }
        uint32_t rb_index = 0;
        if (weight > 0) {
            rb_index = synapse_row_get_ring_buffer_index(time + 1,
                connector->positive_synapse_type, post_index,
                synapse_type_index_bits, synapse_index_bits,
                synapse_delay_mask);
        } else {
            rb_index = synapse_row_get_ring_buffer_index(time + 1,
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
