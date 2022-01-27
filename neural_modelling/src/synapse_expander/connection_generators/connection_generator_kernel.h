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
 * \brief Kernel connection generator implementation
 */

#include <stdbool.h>
#include <synapse_expander/common_kernel.h>
#include <synapse_expander/common_mem.h>
#include <synapse_expander/generator_types.h>

/**
 * \brief The parameters to be passed around for this connector
 */
struct kernel {
	// put in the relevant kernel connector parameters here
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

    // any further parameters required would go here
    // uint32_t allow_self_connections;
};

/**
 * \brief Initialise the convolution-kernel connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_kernel_initialise(void **region) {
    // Allocate the data structure for parameters
    struct kernel *obj = spin1_malloc(sizeof(struct kernel));

    // Copy the parameters into the data structure
    struct kernel *params_sdram = *region;
    // Smaller than standard memcpy()
    *obj = *params_sdram;
    *region = &params_sdram[1];

    log_debug("Kernel connector, m_kernelWidth, m_kernelHeight = %u %u",
    		obj->kernelWidth, obj->kernelHeight);

    return obj;
}

/**
 * \brief Free the convolution-kernel connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_kernel_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief Generate connections with the convolution-kernel connection generator
 * \param[in] generator: The generator to use to generate connections
 * \param[in] pre_slice_start: The start of the slice of the pre-population
 *                             being generated
 * \param[in] pre_slice_count: The number of neurons in the slice of the
 *                             pre-population being generated
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] post_slice_start: The start of the slice of the post-population
 *                              being generated
 * \param[in] post_slice_count: The number of neurons in the slice of the
 *                              post-population being generated
 * \param[in] max_row_length: The maximum number of connections to generate
 * \param[in,out] indices: An array into which the core-relative post-indices
 *                         should be placed.  This will be initialised to be
 *                         \p max_row_length in size
 * \return The number of connections generated
 */
static uint32_t connection_generator_kernel_generate(
        void *generator, UNUSED uint32_t pre_slice_start,
        UNUSED uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    log_debug("Generating for %u", pre_neuron_index);

    // If no space, generate nothing
    if (max_row_length < 1) {
    	return 0;
    }

    struct kernel *obj = generator;

    // start n_conns at zero
    uint32_t n_conns = 0;

    uint16_t pre_c = 0;
    uint16_t pre_r = uidiv(pre_neuron_index, obj->preWidth, &pre_c);

    // Check whether these coordinates should be included based on step functions
    if (!(((pre_r - obj->startPreHeight) % obj->stepPreHeight == 0) &&
    		((pre_c - obj->startPreWidth) % obj->stepPreWidth == 0))) {
    	return 0;
    }

    uint16_t hlf_kw = obj->kernelWidth >> 1;
    uint16_t hlf_kh = obj->kernelHeight >> 1;
    int16_t k_r, k_c;
    for (uint16_t i = 0; i < post_slice_count; i++) {
        uint16_t post_r, post_c; //post raw
        uint16_t pac_r, pac_c; // post as common
        int16_t pap_r, pap_c; // post as pre
        post_r = uidiv(post_slice_start + i, obj->postWidth, &post_c);

        //move post coords into common coordinate system
        post_in_pre_world(
        		post_r, post_c, obj->startPostHeight, obj->startPostWidth,
				obj->stepPostHeight, obj->stepPostWidth, &pac_r, &pac_c);

        //move common to pre coords
        pre_in_post_world(
                pac_r, pac_c, obj->startPreHeight, obj->startPreWidth,
                obj->stepPreHeight, obj->stepPreWidth, &pap_r, &pap_c);

        int16_t r_diff = (int16_t) pap_r - (int16_t) pre_r;
        int16_t c_diff = (int16_t) pap_c - (int16_t) pre_c;

        k_r = hlf_kh - r_diff;
        k_c = hlf_kw - c_diff;

        if ((0 <= k_r) && (k_r < obj->kernelHeight) && (0 <= k_c)
                && (k_c < obj->kernelWidth)) {
            indices[n_conns++] = i;
        }
    }

    return n_conns;
}
