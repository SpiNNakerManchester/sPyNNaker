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
 * \file
 * \brief Parameter generator implementation for convolution kernels
 */
#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <synapse_expander/common_kernel.h>
#include <synapse_expander/common_mem.h>
#include <synapse_expander/generator_types.h>

//! Convolution kernel parameter generator configuration
struct param_generator_kernel {
    uint16_t commonWidth;
    uint16_t commonHeight;

    //! Prepopulation grid width
    uint16_t preWidth;
    //! Prepopulation grid height
    uint16_t preHeight;
    //! Postpopulation grid width
    uint16_t postWidth;
    //! Postpopulation grid height
    uint16_t postHeight;

    //! Prepopulation grid X offset
    uint16_t startPreWidth;
    //! Prepopulation grid Y offset
    uint16_t startPreHeight;
    //! Postpopulation grid X offset
    uint16_t startPostWidth;
    //! Postpopulation grid Y offset
    uint16_t startPostHeight;

    //! Prepopulation grid X step
    uint16_t stepPreWidth;
    //! Prepopulation grid Y step
    uint16_t stepPreHeight;
    //! Postpopulation grid X step
    uint16_t stepPostWidth;
    //! Postpopulation grid Y step
    uint16_t stepPostHeight;

    //! Convolution kernel grid width
    uint16_t kernelWidth;
    //! Convolution kernel grid height
    uint16_t kernelHeight;

    //! Offset into the postpopulation that the current core's slice starts at
    uint32_t post_slice_start;
};

//! Implementation of the state of the convolution kernel parameter generator
struct all_kernel_params {
    //! Configuration descriptor
    struct param_generator_kernel params;
    //! Array of values in the convolution kernel
    accum *values;
};

/**
 * \brief How to initialise the convolution kernel parameter generator
 * \param[in,out] region: Region to read setup from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *param_generator_kernel_initialize(address_t *region) {
    struct all_kernel_params *obj = spin1_malloc(sizeof(struct all_kernel_params));
    struct param_generator_kernel *params_sdram = (void *) *region;
    fast_memcpy(&obj->params, params_sdram++, sizeof(*params_sdram));
    *region = (void *) params_sdram;

    obj->values = (accum *) params_sdram;
    *region += obj->params.kernelHeight * obj->params.kernelWidth;

    log_debug("Kernel param generator; kernelWidth, kernelHeight = %u,%u",
    		obj->params.kernelWidth, obj->params.kernelHeight);

    return obj;
}

/**
 * \brief How to free any data for the convolution kernel parameter generator
 * \param[in] generator: The generator to free
 */
static void param_generator_kernel_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to generate values with the convolution kernel parameter generator
 * \param[in] generator: The generator to use to generate values
 * \param[in] n_synapses: The number of values to generate
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] indices: The \p n_indices post-neuron indices for each connection
 * \param[out] values: An array into which to place the values; will be
 *                     \p n_indices in size
 */
static void param_generator_kernel_generate(
        void *generator, uint32_t n_synapses,
        uint32_t pre_neuron_index, uint16_t *indices, accum *values) {
    struct all_kernel_params *obj = generator;
    struct param_generator_kernel *params = &obj->params;
    uint16_t pre_c = 0;
    uint16_t pre_r = uidiv(pre_neuron_index, params->preWidth, &pre_c);

    // Check whether these coordinates should be included based on step functions
    if (!(((pre_r - params->startPreHeight) % params->stepPreHeight == 0) &&
    		((pre_c - params->startPreWidth) % params->stepPreWidth == 0))) {
    	return;
    }

    uint16_t hlf_kw = params->kernelWidth >> 1;
    uint16_t hlf_kh = params->kernelHeight >> 1;
    int16_t k_r, k_c;
    for (uint16_t i = 0; i < n_synapses; i++) {
        uint16_t post_r, post_c; //post raw
        uint16_t pac_r, pac_c; // post as common
        int16_t pap_r, pap_c; // post as pre
        post_r = uidiv(params->post_slice_start + indices[i],
                params->postWidth, &post_c);

        //move post coords into common coordinate system
        post_in_pre_world(post_r, post_c, params->startPostHeight,
                params->startPostWidth, params->stepPostHeight,
                params->stepPostWidth, &pac_r, &pac_c);

        //move common to pre coords
        pre_in_post_world(
                pac_r, pac_c, params->startPreHeight, params->startPreWidth,
                params->stepPreHeight, params->stepPreWidth, &pap_r, &pap_c);

        int16_t r_diff = (int16_t) pap_r - (int16_t) pre_r;
        int16_t c_diff = (int16_t) pap_c - (int16_t) pre_c;

        k_r = hlf_kh - r_diff;
        k_c = hlf_kw - c_diff;

        if ((0 <= k_r) && (k_r < params->kernelHeight) && (0 <= k_c)
                && (k_c < params->kernelWidth)) {
            values[i] = obj->values[k_r * params->kernelWidth + k_c];
            //      LOG_PRINT(LOG_LEVEL_INFO, "val = %5.6k", output[i]);
        } else {
            log_error("Kernel coordinates off range (%d, %d)", k_r, k_c);
        }
    }
}
