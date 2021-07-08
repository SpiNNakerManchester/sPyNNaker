/*
 * Copyright (c) 2020 The University of Sussex, Garibaldi Pineda Garcia
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

#include "local_only.h"
#include "local_only_typedefs.h"
#include <stdlib.h>
#include <common/neuron-typedefs.h>
#include <debug.h>
#include "../population_table/population_table.h"
#include "../neuron.h"

//! \file DTCM-only convolutional implementation of custom rows

// how many 32-bit words will we use for pre/post shapes
#define LEN_SHAPE_DATA (3)
#define DEC_BITS (11)

static uint32_t num_connectors = 0;
static uint32_t *jumps = NULL;
static int16_t** weights = NULL;
static uint32_t n_words = 0;
static lc_neuron_id_t* pre_starts = NULL;
static lc_neuron_id_t* pre_ends = NULL;
static int16_t *pre2post_rc = NULL;
static lc_neuron_id_t n_post = 0;
static lc_neuron_id_t post_start = 0; // post start
static lc_neuron_id_t post_end = 0; // post end
static post_width = 0;
static uint32_t post_shift = 0;
static uint32_t post_use_row_msb = 0;

//! \brief Do a mapping from pre to post 2D spaces to 1D post after pooling
static inline lc_dim_t local_only_map_pre_id_to_post_id(lc_dim_t pre){
    return pre2post_rc[pre];
}

lc_weight_t from16_to_32(int16_t v){
//    return (((int32_t) v) << SHIFT);
    lc_weight_t v32 = (int32_t)(v);
//    log_info("value int32 %d", v32);
//    v32 <<= SHIFT;
    v32 >>= DEC_BITS;
//    log_info("value int32 %d, %k", v32, (lc_weight_t)(v32));
    return (v32);
}

//! \brief Load the required data into DTCM.
bool local_only_initialise(address_t sdram_address){
    log_info("+++++++++++++++++ POOL-DENSE init ++++++++++++++++++++");
    log_info("SDRAM address is 0x%08x", sdram_address);
    if (sdram_address == NULL) {
        log_error("Invalid local-only address in SDRAM.");
        return false;
    }
    // total incoming local-only connections data size
    n_words = *((uint32_t*)sdram_address++);
    log_info("num words %d", n_words);
    if (n_words == 0) {
        return false;
    }

    num_connectors = *((uint32_t*)sdram_address++);
    if (num_connectors == 0 && n_words > 0) {
        return false;
    }
    log_info("num connectors = %u", num_connectors);

    post_use_row_msb = *((uint32_t*)sdram_address++);
    log_info("Post use row as msb = %u", post_use_row_msb);

    post_shift = *((uint32_t*)sdram_address++);
    log_info("Post shift is %u", post_shift);

    pre_starts = (lc_neuron_id_t *)spin1_malloc(
                                    num_connectors * sizeof(lc_neuron_id_t));
    if (pre_starts == NULL) {
        log_error("Can't allocate memory for pre slices starts.");
        return false;
    }

    pre_ends = (lc_neuron_id_t *)spin1_malloc(
                                    num_connectors * sizeof(lc_neuron_id_t));
    if (pre_ends == NULL) {
        log_error("Can't allocate memory for pre slices ends.");
        return false;
    }

    weights = (int16_t **)spin1_malloc(num_connectors * sizeof(int16_t *));
    if (weights == NULL) {
        log_error(
            "Could not initialise dense weights pointer (size = %u)",
            num_connectors);
        return false;
//            rt_error(RTE_SWERR);
    }


    uint32_t n_pre = 0;
    uint32_t n_pre_weights = 0;
    uint32_t idx = 0;
    address_t _address = sdram_address;
    for (uint32_t conn_idx = 0; conn_idx < num_connectors; conn_idx++) {
        // how many elements are in a single connector data
        uint32_t n_elem = *((uint32_t*)_address++);

        log_info("CONNECTOR %u\nNum elem %d", conn_idx, n_elem);
        log_info("sark_heap_max = %u", sark_heap_max(sark.heap, 0));

        uint32_t start = *((uint32_t*)_address++);
        pre_starts[conn_idx] = start >> 16;
        pre_ends[conn_idx] = start & 0xFFFF;
        log_info("Pre %u start is %u", conn_idx, pre_starts[conn_idx]);
        log_info("Pre %u end is %u", conn_idx, pre_ends[conn_idx]);

        start = *((uint32_t*)_address++);
        post_start = start >> 16;
        post_end = start & 0xFFFF;
        log_info("Post start %d", post_start);
        log_info("Post end %d", post_end);
        n_post = post_end - post_start;

        // shapes are 16-bit uints, hopefully enough for future too?
        uint16_t *p = ((uint16_t*)(_address));
        // todo: can this be done with just a single memcpy?
        // todo: does it matter?
        uint16_t tmp_width = *((lc_dim_t*)(p++));
        uint16_t tmp_height = *((lc_dim_t*)(p++));
        log_info("pre width %u, height %u", tmp_width, tmp_height);
        n_pre = tmp_width * tmp_height;
        post_width = *((lc_dim_t*)(p++));
//        tmp_height = *((lc_dim_t*)(p++));
//        log_info("post pool width %u, height %u", post_width, tmp_height);
        log_info("n_pre %u, post_width %u", n_pre, post_width);
        p++;
        tmp_width = *((lc_dim_t*)(p++));
        tmp_height = *((lc_dim_t*)(p++));
        log_info("weights rows %u, cols %u", tmp_height, tmp_width);

//        uint32_t n_weights = tmp_width * tmp_height;
        n_pre_weights = tmp_height;//pre_ends[conn_idx] - pre_starts[conn_idx];
        uint32_t n_weights = n_pre_weights * n_post;
        log_info("n_pre %u, n_post %u", n_pre_weights, n_post);
        log_info("Num weights %u", n_weights);

        weights[conn_idx] = (int16_t *)spin1_malloc(n_weights * sizeof(int16_t));
        if (weights[conn_idx] == NULL) {
            log_error(
                "Could not initialise dense layer weights (size = %u)",
                n_weights);
            return false;
    //            rt_error(RTE_SWERR);
        }

        uint32_t *p32 = _address + LEN_SHAPE_DATA;
//        for (lc_dim_t r=0; r < n_pre_weights; r++) {
//            for (lc_dim_t c=0; c < n_post; c++) {
        for (uint32_t w_idx = 0; w_idx < n_weights; w_idx++){
//                uint32_t w_idx = r * tmp_width + c;
            uint32_t r = (w_idx) / n_post;
            uint32_t c = (w_idx) % n_post;
            // memory addressing trickery - basically interpret bits as something else
            // get address, then convert pointer, then get contents
            uint32_t v = 0;
            if (w_idx % 2 == 0){
                v = (uint32_t)(p32[w_idx/2] >> 16);
            } else {
                v = (uint32_t)(p32[w_idx/2] & 0xFFFF);
            }
            uint16_t v16 = (uint16_t)(v);
            int16_t iv16 = *(int16_t *)(&v16);

            weights[conn_idx][w_idx] = iv16;
//            weights[conn_idx][w_idx] = ((int32_t)(iv16));
//            weights[conn_idx][w_idx] >>= DEC_BITS;

//                weights[conn_idx][w_idx] = *( (lc_weight_t *)(&p32[w_idx]) );
                if ((r == 0 && c == 0) ||
                    (r == (n_pre_weights - 1) && c == (n_post - 1)))
                {
                lc_weight_t w32 = from16_to_32(weights[conn_idx][w_idx]);
                log_info("w(%d, %d)[%u] = fixed-point %k %u %d",
                r, c,

                w_idx,
                w32,
                v16,
                weights[conn_idx][w_idx]
                );
            }
//            }
        }
        _address = p32 + n_weights/2 + (n_weights % 2);

    }

    log_info("\n");
    log_info("\n Num pre %d", n_pre);
    uint32_t *p32 = _address;
    uint32_t n_translations = *p32++;
    log_info("num translations %d", n_translations);

    pre2post_rc = (int16_t *)spin1_malloc(2 * n_translations * sizeof(int16_t));
    if (pre2post_rc == NULL) {
        log_error(
            "Could not initialise convolution pre ids to post "
            "coordinate array (size = %u)",
            n_translations * 2);
        return false;
    }


//    int post_lim = n_pre/2 + (n_pre%2 > 0);
    int post_lim = n_translations;
    for (size_t idx = 0; idx < post_lim; idx++) {
        uint32_t idx16 = idx * 2;
        log_info("data %u :> %u", idx, p32[idx]);
        pre2post_rc[idx16] = (uint16_t)(p32[idx] >> 16);
        pre2post_rc[idx16 + 1] = (uint16_t)(p32[idx] & 0xFFFF);
        log_info("pre to post(r,c) %u => %u",
            idx16, pre2post_rc[idx16]
        );
//        if ((idx16 + 1) == n_pre) {
//            break;
//        }
        log_info("pre to post(r,c) %u => %u",
            idx16+1, pre2post_rc[idx16+1]
        );

    }

    return true;
}

//! \brief Check if we found the correct data in SDRAM
bool local_only_is_compatible(void){
    return (n_words > 0);
}

bool local_only_skip_synapse_timestep(void){
    return (n_words > 0);
}

//! \brief Process incoming spikes. In this implementation we need to:
//! 1. Check if it's in the population table
//! 2. Convert the relative (per core) Id to a global (per population) one
//! 3. Obtain the post-ids and weights which will be reached by the spike/kernel
//!    combination.
//! 4. Add the weights to the appropriate current buffers
void local_only_process_spike(uint32_t key, UNUSED uint32_t payload){
    synaptic_row_t dummy = 1234;
    uint32_t conn_jump = 0;
    size_t pre_id_relative = 0;
    bool success = false;

    // see if spike key can be found in the population table,
    // get the number of incoming connector (conn_jump) and the
    // relative (to slice beginning) pre-synaptic neuron id
    success = population_table_get_first_address(
        key, &dummy, &pre_id_relative);

    // if the key was found in the pop table, then add current to
    // post-synaptic neuron
    if (success) {
        conn_jump = pre_id_relative >> 16;
        pre_id_relative &= 0xFFFF;


        // compute the real pre-syn id (population id)
        lc_neuron_id_t pre_id = pre_id_relative + pre_starts[conn_jump];
//        log_info("real pre id %u\n", pre_id);
//        log_info(
//            "key %u\tpayload %d\tjump %u\tpre_rel %u\tpre abs %u\tsuccess = %u",
//            key, payload, conn_jump, pre_id_relative, pre_id, success);

        lc_dim_t row = (local_only_map_pre_id_to_post_id(pre_id) * n_post);

        // todo: starts at shapes.start and should also have a cap on end!
        // add the weight to each of the post neurons
        for (lc_dim_t i=0; i<n_post; i++) {
              lc_weight_t w = from16_to_32(weights[conn_jump][row + i]);
//            log_info("post %u, weight fixed-point s1615 %k",
//                i, weights[conn_jump][row + i]);
//            if (pre_id >= post_start) {
                neuron_add_inputs(
                    0, // only one synapse type to save space
                    i,
                    w
                );//*payload);
//            }

        }
    }
}
