/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

    //! True if weights are present in the array below
    uint16_t weightsPresent;
    //! True if delays are present in the array below
    uint16_t delaysPresent;

    //! Kernel weights and delays
    //! This is an array of up to kernel width x height x 2
    //! (one for each of weight and delay) depending on above flags
    accum kernelWeightsAndDelays[];
};

/**
 * \brief Initialise the convolution-kernel connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_kernel_initialise(void **region) {
    struct kernel *params_sdram = *region;

    // Allocate the data structure for parameters
    uint32_t kernelSize = params_sdram->kernelWidth * params_sdram->kernelHeight;
    uint32_t size = sizeof(struct kernel);
    uint32_t extra = 0;
    if (params_sdram->weightsPresent) {
    	size += kernelSize * sizeof(accum);
    	extra += kernelSize;
    }
    if (params_sdram->delaysPresent) {
    	size += kernelSize * sizeof(accum);
    	extra += kernelSize;
    }
    struct kernel *obj = spin1_malloc(size);

    // Copy the parameters into the data structure
    spin1_memcpy(obj, params_sdram, size);
    *region = &(params_sdram->kernelWeightsAndDelays[extra]);

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
static bool connection_generator_kernel_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {

    struct kernel *obj = generator;
    uint16_t hlf_kw = obj->kernelWidth >> 1;
    uint16_t hlf_kh = obj->kernelHeight >> 1;
    int16_t k_r, k_c;
    uint32_t k_offset = obj->kernelWidth * obj->kernelHeight;

    // Get the actual ranges to generate within
    uint32_t post_start = max(post_slice_start, post_lo);
    uint32_t post_end = min(post_slice_start + post_slice_count - 1, post_hi);

    // Go through and find the coordinates needed
    for (uint32_t pre = pre_lo; pre <= pre_hi; pre++) {
        uint16_t pre_c = 0;
        uint16_t pre_r = uidiv(pre, obj->preWidth, &pre_c);
        for (uint32_t post = post_start; post <= post_end; post++) {
            uint16_t post_r, post_c; //post raw
            uint16_t pac_r, pac_c; // post as common
            int16_t pap_r, pap_c; // post as pre
            post_r = uidiv(post, obj->postWidth, &post_c);

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
                uint32_t local_post = post - post_slice_start;
                accum weight;
                accum delay;
                uint32_t k = (k_r * obj->kernelWidth) + k_c;
                if (obj->weightsPresent && obj->delaysPresent) {
                    weight = obj->kernelWeightsAndDelays[k];
                    delay = obj->kernelWeightsAndDelays[k + k_offset];
                } else if (obj->weightsPresent) {
                    weight = obj->kernelWeightsAndDelays[k];
                    delay = param_generator_generate(delay_generator);
                } else if (obj->delaysPresent) {
                    weight = param_generator_generate(weight_generator);
                    delay = obj->kernelWeightsAndDelays[k];
                } else {
                    weight = param_generator_generate(weight_generator);
                    delay = param_generator_generate(delay_generator);
                }
                if (!matrix_generator_write_synapse(
                        matrix_generator, pre, local_post,
                        weight, rescale_delay(delay, timestep_per_delay),
						weight_scale)) {
                    log_error("Matrix size is wrong!");
                    return false;
                }
            }
        }
    }
    return true;
}
