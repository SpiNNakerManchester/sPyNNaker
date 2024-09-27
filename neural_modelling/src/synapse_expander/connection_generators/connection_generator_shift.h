/*
 * Copyright (c) 2017 The University of Manchester
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

/**
 * \file
 * \brief Shift Connection generator implementation
 */

#include <synapse_expander/generator_types.h>

//! \brief The parameters to be passed around for this connector
struct shift {
	// Amount to shift the pre by to get the post
    int32_t shift;
    // Whether to wrap around the post values or just clip
    uint32_t wrap;
    // The group size to consider for the shift
    uint32_t n_neurons_per_group;

};


/**
 * \brief Initialise the shift connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_shift_initialise(UNUSED void **region) {
	// Allocate the data structure for parameters
	struct shift *params = spin1_malloc(sizeof(struct shift));
	struct shift *params_sdram = *region;

	// Copy the parameters into the data structure
	*params = *params_sdram;
	*region = &params_sdram[1];

	log_debug("Shift connector, shift = %u, wrap = %u, n_neurons_per_group = %u",
			params->shift, params->wrap, params->n_neurons_per_group);

	return params;
}

/**
 * \brief Free the shift connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_shift_free(UNUSED void *generator) {
    // Nothing to do
}

/**
 * \brief Generate connections with the shift connection generator
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
static bool connection_generator_shift_generate(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, UNUSED uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator) {

	struct shift *obj = generator;

	// Get the actual ranges to generate within
	uint32_t post_start = max(post_slice_start, post_lo);
	uint32_t post_end = min(post_slice_start + post_slice_count - 1, post_hi);

	// Work out where we are in the generation
	// We need to connect each pre-neuron to each post-neuron in each group
	// (but not to itself).  We are currently generating a subset of the post
	// neurons, so we need to work out which group we are in within that subset,
	// and which is the first post-neuron in the group that we are generating
	// for now.
	uint32_t post_group;
	uint32_t post_value;
	div_mod(post_start, obj->n_neurons_per_group, &post_group, &post_value);

	// Work out where the pre-neurons start and end for the group that we are
	// in at the start of the post-neurons.
	uint32_t pre_start = pre_lo + post_group * obj->n_neurons_per_group;
	uint32_t pre_end = min(pre_start + obj->n_neurons_per_group - 1, pre_hi);

	// Go through the post neurons in this slice
	for (uint32_t post = post_start; post <= post_end; post++) {
		uint32_t local_post = post - post_slice_start;

		// Find the pre that occurs after shifting; as the shift is post from
		// pre, we subtract it to get pre from post (notee it might be negative already)
		int32_t pre = post - obj->shift;
		bool use = true;
		if (pre < (int32_t) pre_start) {
			if (obj->wrap) {
				pre += obj->n_neurons_per_group;
			} else {
				use = false;
			}
		} else if (pre > (int32_t) pre_end) {
			if (obj->wrap) {
				pre -= obj->n_neurons_per_group;
			} else {
				use = false;
			}
		}

		if (use) {
			accum weight = param_generator_generate(weight_generator);
			uint16_t delay = rescale_delay(
					param_generator_generate(delay_generator), timestep_per_delay);
			if (!matrix_generator_write_synapse(matrix_generator, (uint32_t) pre,
					local_post, weight, delay, weight_scale)) {
				log_error("Matrix not sized correctly!");
				return false;
			}
		}

		// Work out next loop iteration.  If we have reached the end of a group
		// of values, we need to move onto the next group.
		post_value += 1;
		if (post_value == obj->n_neurons_per_group) {
			post_value = 0;
			pre_start += obj->n_neurons_per_group;
			pre_end = min(pre_start + obj->n_neurons_per_group - 1, pre_hi);
			if (pre_start > pre_hi) {
				break;
			}
		}
	}

	return true;
}
