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
 * \brief One-to-One Connection generator implementation
 */

#include <synapse_expander/generator_types.h>

/**
 * \brief Initialise the one-to-one connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_one_to_one_initialise(UNUSED void **region) {

    log_debug("One to one connector");

    return NULL;
}

/**
 * \brief Free the one-to-one connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_one_to_one_free(UNUSED void *generator) {
    // Nothing to do
}

/**
 * \brief Generate connections with the one-to-one connection generator
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
static bool connection_generator_one_to_one_generate(
        UNUSED void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {

	// First check if any of the range to generate is on this slice
	uint32_t post_slice_end = post_slice_start + post_slice_count - 1;
	if (post_lo > post_slice_end || post_hi < post_slice_start) {
		return true;
	}

	// Find the start and end on the current slice
	uint32_t post_start = max(post_slice_start, post_lo);
	uint32_t post_end = min(post_slice_end, post_hi);

	// Find the offset and length on the current slice
	uint32_t offset = post_start - post_lo;
	uint32_t length = post_end - post_start;

	// Work out the pre start and end to be generated
	uint32_t pre_start = pre_lo + offset;
	uint32_t pre_end = min(pre_lo + length, pre_hi);

    log_info("Post slice start %u, post_slice_count %u", post_slice_start, post_slice_count);
    log_info("Post lo %u, post hi %u", post_lo, post_hi);
    log_info("Pre lo %u, pre_hi %u", pre_lo, pre_hi);
    log_info("Post start %u, post end %u, pre_start %u, pre_end %u", post_start, post_end, pre_start, pre_end);

    for (uint32_t pre = pre_start, post = post_start; pre <= pre_end; pre++, post++) {
        uint32_t local_post = post - post_slice_start;
        uint16_t weight = rescale_weight(
                param_generator_generate(weight_generator), weight_scale);
        uint16_t delay = rescale_delay(
                param_generator_generate(delay_generator), timestep_per_delay);
        if (!matrix_generator_write_synapse(matrix_generator, pre, local_post,
                weight, delay)) {
            log_error("Matrix size is wrong!");
            return false;
        }
    }
    return true;
}
