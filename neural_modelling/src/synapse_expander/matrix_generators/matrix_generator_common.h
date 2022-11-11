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
 * \dir
 * \brief Synaptic matrix generators
 * \file
 * \brief Common functions for matrix generation
 */

#ifndef __MATRIX_GENERATOR_COMMON_H__
#define __MATRIX_GENERATOR_COMMON_H__

#include <debug.h>

//! The number of header words per row
#define N_HEADER_WORDS 3

/**
 * \brief A converted final delay value and delay stage
 */
struct delay_value {
    uint16_t delay;
    uint16_t stage;
};

/**
 * \brief Get a converted delay value and stage
 * \param[in] delay_value: The value to convert
 * \param[in] max_stage: The maximum delay stage allowed
 * \param[in] max_delay_per_stage: The max delay in a delay stage
 * \return The converted delay value
 */
static struct delay_value get_delay(
        uint16_t delay_value, uint32_t max_stage,
        uint32_t max_delay_per_stage) {
    uint16_t delay = delay_value;

    // Ensure delay is at least 1
    if (delay < 1) {
        log_debug("Delay of %u is too small", delay);
        delay = 1;
    }

    // Ensure that the delay is less than the maximum
    uint16_t stage = (delay - 1) / max_delay_per_stage;
    if (stage >= max_stage) {
        log_debug("Delay of %u is too big", delay);
        stage = max_stage - 1;
        delay = (stage * max_delay_per_stage);
    }

    // Get the remainder of the delay
    delay = ((delay - 1) % max_delay_per_stage) + 1;
    return (struct delay_value) {.delay = delay, .stage = stage};
}

/**
 * \brief Get a synaptic row for a given neuron
 * \param[in] synaptic_matrix the address of the synaptic matrix
 * \param[in] max_row_n_words the maximum number of words (excluding headers)
 *                            in each row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \return A pointer to the row of the matrix to write to
 */
static void *get_row(uint32_t *synaptic_matrix, uint32_t max_row_n_words,
        uint32_t pre_index) {
    uint32_t idx = pre_index * (max_row_n_words + N_HEADER_WORDS);
    return &synaptic_matrix[idx];
}

/**
 * \brief Get a delayed synaptic row for a given neuron and delay stage
 * \param[in] delayed synaptic_matrix the address of the delayed synaptic matrix
 * \param[in] max_delayed_row_n_words the maximum number of words (excluding headers)
 *                                    in each delayed row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \param[in] delay_stage the delay stage, where 0 means the undelayed stage
 * \param[in] n_pre_neurons_per_core The number of neurons per core in the pre-population
 * \param[in] max_delay_stage The maximum delay stage
 * \param[in] n_pre_neurons The number of neurons in the pre-population
 * \return A pointer to the row of the delayed matrix to write to
 */
static void *get_delay_row(uint32_t *delayed_synaptic_matrix,
        uint32_t max_delayed_row_n_words, uint32_t pre_index, uint32_t delay_stage,
        uint32_t n_pre_neurons_per_core, uint32_t max_delay_stage, uint32_t n_pre_neurons) {
	// Work out which core the pre-index is on
	uint32_t core = 0;
	uint32_t remaining_pre_neurons = n_pre_neurons;
	while (((core + 1) * n_pre_neurons_per_core) < pre_index) {
		core++;
		remaining_pre_neurons -= n_pre_neurons_per_core;
	}

	// Get the core-local pre-index
	uint32_t local_pre_index = pre_index - (core * n_pre_neurons_per_core);

	// Find the number of neurons on *this* core, which might be the last core
	// (and therefore have less of them)
	uint32_t n_neurons_on_core = n_pre_neurons_per_core;
	if (remaining_pre_neurons < n_pre_neurons_per_core) {
		n_neurons_on_core = remaining_pre_neurons;
	}

	// Work out the *delay* neurons per pre-delay-core
	uint32_t n_delay_neurons_per_core = n_pre_neurons_per_core * (max_delay_stage - 1);

	// With these we can now work out the number of rows associated with all the
	// previous cores, and the delay row index for this core
	uint32_t delay_core_index = core * n_delay_neurons_per_core;
	uint32_t delay_local_index = ((delay_stage - 1) * n_neurons_on_core) + local_pre_index;

	// That then finally gives us the delay pre-row
    uint32_t pre_row = delay_core_index + delay_local_index;
	uint32_t idx = pre_row * (max_delayed_row_n_words + N_HEADER_WORDS);
    return &delayed_synaptic_matrix[idx];
}


#endif // __MATRIX_GENERATOR_COMMON_H__
