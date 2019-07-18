/*
 * Copyright (c) 2017-2019 The University of Manchester
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

/**
 *! \file
 *! \brief Kernel connection generator implementation
 */

#include <stdbool.h>
#include <synapse_expander/common_kernel.h>

/**
 *! \brief The parameters to be passed around for this connector
 */
typedef struct kernel {
	// put in the relevant kernel connector parameters here
    uint16_t m_commonWidth;
    uint16_t m_commonHeight;

    uint16_t m_preWidth;
    uint16_t m_preHeight;
    uint16_t m_postWidth;
    uint16_t m_postHeight;

    uint16_t m_startPreWidth;
    uint16_t m_startPreHeight;
    uint16_t m_startPostWidth;
    uint16_t m_startPostHeight;

    uint16_t m_stepPreWidth;
    uint16_t m_stepPreHeight;
    uint16_t m_stepPostWidth;
    uint16_t m_stepPostHeight;

    uint16_t m_kernelWidth;
    uint16_t m_kernelHeight;

    // any further parameters required would go here
    // uint32_t allow_self_connections;
} kernel_connection_t;

static void *connection_generator_kernel_initialise(address_t *region) {
    // Allocate the data structure for parameters
    kernel_connection_t *params = spin1_malloc(sizeof(kernel_connection_t));

    // Copy the parameters into the data structure
    kernel_connection_t *params_sdram = (kernel_connection_t *) *region;
    spin1_memcpy(params, params_sdram, sizeof(kernel_connection_t));
    log_debug("Kernel connector, m_kernelWidth, m_kernelHeight = %u %u",
    		params->m_kernelWidth, params->m_kernelHeight);

    *region = (address_t) &params_sdram[1];
    return params;
}

static void connection_generator_kernel_free(void *data) {
    sark_free(data);
}

static uint32_t connection_generator_kernel_generate(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    kernel_connection_t *params = data;

    use(pre_slice_start);
    use(pre_slice_count);

    log_debug("Generating for %u", pre_neuron_index);

    // If no space, generate nothing
    if (max_row_length < 1) {
    	return 0;
    }

    // start n_conns at zero
    uint32_t n_conns = 0;

    uint16_t pre_c = 0;
    uint16_t pre_r = uidiv(pre_neuron_index, params->m_preWidth, &pre_c);

    uint16_t hlf_kw = params->m_kernelWidth >> 1;
    uint16_t hlf_kh = params->m_kernelHeight >> 1;
    int16_t k_r, k_c;
    for (uint16_t i = 0; i < post_slice_count; i++) {
        uint16_t post_r, post_c; //post raw
        uint16_t pac_r, pac_c; // post as common
        int16_t pap_r, pap_c; // post as pre
        post_r = uidiv(post_slice_start + i, params->m_postWidth, &post_c);

        //move post coords into common coordinate system
        post_in_pre_world(post_r, post_c, params->m_startPostHeight,
                params->m_startPostWidth, params->m_stepPostHeight,
                params->m_stepPostWidth, &pac_r, &pac_c);

        //move common to pre coords
        pre_in_post_world(
                pac_r, pac_c, params->m_startPreHeight, params->m_startPreHeight,
                params->m_stepPreHeight, params->m_stepPreWidth, &pap_r, &pap_c);

        int16_t r_diff = (int16_t) pap_r - (int16_t) pre_r;
        int16_t c_diff = (int16_t) pap_c - (int16_t) pre_c;

        k_r = hlf_kh - r_diff;
        k_c = hlf_kw - c_diff;

        if ((0 <= k_r) && (k_r < params->m_kernelHeight) && (0 <= k_c)
                && (k_c < params->m_kernelWidth)) {
            indices[n_conns++] = i;
        }
    }

    return n_conns;
}
