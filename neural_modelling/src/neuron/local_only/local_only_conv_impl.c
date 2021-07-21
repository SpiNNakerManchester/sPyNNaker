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
    uint32_t col_mask;
    uint32_t col_shift;
    uint32_t row_mask;
    uint32_t row_shift;
} source_key_info;

// A reciprocal of a 16-bit signed integer will have 1 sign bit, 1 integer bit
// and 14 fractional bits to allow 1 to be properly represented
#define RECIP_FRACT_BITS 14

// One per connector
typedef struct {
    source_key_info key_info;
    lc_coord_t pre_start;
    lc_shape_t pre_shape;
    lc_shape_t kernel;
    lc_shape_t padding;
    lc_coord_t recip_strides;
    lc_coord_t recip_pool_strides;
    uint16_t positive_synapse_type;
    uint16_t negative_synapse_type;
    lc_weight_t weights[]; // n_weights = next_even(kernel.width * kernel.height)
} connector;

typedef struct {
    lc_coord_t post_start;
    lc_coord_t post_end;
    lc_shape_t post_shape;
    uint32_t n_connectors;
    // In SDRAM, below here is the following:
    // connector connectors[n_connectors]
} conv_config;

// The main configuration data
static conv_config config;

// The per-connection data
static connector** connectors;

//! \brief Load the required data into DTCM.
bool local_only_impl_initialise(void *address){
    log_info("+++++++++++++++++ CONV init ++++++++++++++++++++");
    conv_config* sdram_config = address;
    config = *sdram_config;

    log_info("post_start = %u, %u, post_end = %u, %u, post_shape = %u, %u",
            config.post_start.col, config.post_start.row,
            config.post_end.col, config.post_end.row,
            config.post_shape.width, config.post_shape.height);
    log_info("num connectors = %u", config.n_connectors);
    if (config.n_connectors == 0) {
        return false;
    }

    // Allocate space for connector information and pre-to-post table
    connectors = spin1_malloc(config.n_connectors * sizeof(connectors[0]));
    if (connectors == NULL) {
        log_error("Can't allocate memory for connectors");
        return false;
    }

    // The first connector comes after the configuration in SDRAM
    connector *conn = (connector *) &sdram_config[1];
    for (uint32_t i = 0; i < config.n_connectors; i++) {
        // We need the number of weights to calculate the size
        uint32_t n_weights = conn->kernel.width * conn->kernel.height;
        if (n_weights & 0x1) {
            n_weights += 1;
        }
        uint32_t n_bytes = sizeof(*conn) + (n_weights * sizeof(conn->weights[0]));

        // Copy the data from SDRAM
        connectors[i] = spin1_malloc(n_bytes);
        if (connectors[i] == NULL) {
            log_error("Can't allocate memory for connectors[%u]", i);
            return false;
        }
        spin1_memcpy(connectors[i], conn, n_bytes);

        log_info("Connector %u: key=0x%08x, mask=0x%08x,"
                "col_mask=0x%08x, col_shift=%u, row_mask=0x%08x, row_shift=%u",
                i, connectors[i]->key_info.key, connectors[i]->key_info.mask,
                connectors[i]->key_info.col_mask, connectors[i]->key_info.col_shift,
                connectors[i]->key_info.row_mask, connectors[i]->key_info.row_shift);

        // Move to the next connector; because it is dynamically sized,
        // this comes after the last weight in the last connector
        conn = (connector *) &conn->weights[n_weights];
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

    int32_t kw = connector->kernel.width;
    for (int32_t r = -half_kh, kr = 0; r <= half_kh; r++, kr++) {
        int32_t tmp_row = post_coord.row + r;
        if ((tmp_row < config.post_start.row) || (tmp_row > config.post_end.row)) {
            continue;
        }
        for (int32_t c = -half_kw, kc = 0; c <= half_kw; c++, kc++) {
            int32_t tmp_col = post_coord.col + c;
            if ((tmp_col < config.post_start.col) || (tmp_col > config.post_end.col)) {
                continue;
            }

            // This the neuron id on this core specifically; the neuron
            // will know how to send the spike correctly
            uint32_t post_index =
                ((tmp_row - config.post_start.row) * config.post_shape.width)
                    + (tmp_col - config.post_start.col);
            uint32_t k = (kr * kw) + kc;
            lc_weight_t weight = connector->weights[k++];
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

static inline bool key_to_index_lookup(uint32_t spike, connector **connector,
        uint32_t *core_local_col, uint32_t *core_local_row) {
    uint32_t imin = 0;
    uint32_t imax = config.n_connectors;

    while (imin < imax) {
        uint32_t imid = (imax + imin) >> 1;
        source_key_info entry = connectors[imid]->key_info;
        if ((spike & entry.mask) == entry.key) {
            *connector = connectors[imid];
            *core_local_col = (spike & entry.col_mask) >> entry.col_shift;
            *core_local_row = (spike & entry.row_mask) >> entry.row_shift;
            return true;
        } else if (entry.key < spike) {

            // Entry must be in upper part of the table
            imin = imid + 1;
        } else {
            // Entry must be in lower part of the table
            imax = imid;
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
    uint32_t core_local_col;
    uint32_t core_local_row;

    // Lookup the spike, and if found, get the appropriate parts
    if (!key_to_index_lookup(
            spike, &connector, &core_local_col, &core_local_row)) {
        return;
    }

    // compute the population-based coordinates
    lc_coord_t pre_coord = {
            core_local_row + connector->pre_start.row,
            core_local_col + connector->pre_start.col
    };
    log_debug("Received spike %u = %u, %u (Global: %u, %u)", spike, core_local_col, core_local_row,
            pre_coord.col, pre_coord.col);

    // Compute the convolution
    do_convolution_operation(time, pre_coord, connector, ring_buffers);
}
