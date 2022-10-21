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
 * \brief Static synaptic matrix implementation
 */

#include <stdbool.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include "matrix_generator_common.h"
#include <synapse_expander/generator_types.h>
#include <utils.h>

//! The layout of a purely static row of a synaptic matrix.
typedef struct {
    uint32_t plastic_plastic_size;  //!< the plastic-plastic size within a row
    uint32_t fixed_fixed_size;      //!< the fixed-fixed size within a row
    uint32_t fixed_plastic_size;    //!< the fixed-plastic size within a row
    uint32_t fixed_fixed_data[];    //!< the fixed-fixed data within a row
} static_row_t;

//! The number of header words per row
#define N_HEADER_WORDS 3

/**
 * \brief The shift of the weight within a synaptic word
 */
#define SYNAPSE_WEIGHT_SHIFT 16

/**
 * \brief The mask of a weight before shifting
 */
#define SYNAPSE_WEIGHT_MASK 0xFFFF

//! The stored data used to generate rows
typedef struct matrix_generator_static_data {
    union {
        //! The address of the synaptic matrix (once initialised)
        uint32_t *synaptic_matrix;
        //! The offset of the synaptic matrix (as read from SDRAM)
        uint32_t synaptic_matrix_offset;
    };
    union {
        //! The address of the delayed synaptic matrix (once initialised)
        uint32_t *delayed_synaptic_matrix;
        //! The offset of the delayed synaptic matrix (as read from SDRAM)
        uint32_t delayed_matrix_offset;
    };
    //! The maximum number of words (excluding headers) on a row
    uint32_t max_row_n_words;
    //! The maximum number of words (excluding headers) on a delayed row
    uint32_t max_delayed_row_n_words;
    //! The matrix synapse type
    uint32_t synapse_type;
    //! The number of bits needed to represent the synapse type
    uint32_t synapse_type_bits;
    //! The number of bits needed to represent the synapse neuron id
    uint32_t synapse_index_bits;
    //! The maximum delay stage, including 0 for no delay stage
    uint32_t max_stage;
    //! The maximum delay per delay stage in time steps
    uint32_t max_delay_per_stage;
    //! The number of bits needed to represent the maximum delay per stage
    uint32_t delay_bits;
    //! The number of pre-synaptic neurons
    uint32_t n_pre_neurons;
    //! The number of pre-synaptic neurons per core
    uint32_t n_pre_neurons_per_core;
} matrix_genetator_static_data_t;

/**
 * \brief Get a synaptic row for a given neuron
 * \param[in] synaptic_matrix the address of the synaptic matrix
 * \param[in] max_row_n_words the maximum number of words (excluding headers)
 *                            in each row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \return A pointer to the row of the matrix to write to
 */
static static_row_t *get_row(uint32_t *synaptic_matrix, uint32_t max_row_n_words,
        uint32_t pre_index) {
    uint32_t idx = pre_index * (max_row_n_words + N_HEADER_WORDS);
    return (static_row_t *) &synaptic_matrix[idx];
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
 * \return A pointer to the row of the delayed matrix to write to
 */
static static_row_t *get_delay_row(uint32_t *delayed_synaptic_matrix,
        uint32_t max_delayed_row_n_words, uint32_t pre_index, uint32_t delay_stage,
        uint32_t n_pre_neurons_per_core, uint32_t max_delay_stage) {
	// Work out which core the pre-index is on
	uint32_t core = 0;
	while (((core + 1) * n_pre_neurons_per_core) < pre_index) {
		core++;
	}
	uint32_t local_pre_index = pre_index - (core * n_pre_neurons_per_core);
	uint32_t n_delay_neurons_per_core = n_pre_neurons_per_core * (max_delay_stage - 1);
	uint32_t delay_core_index = core * n_delay_neurons_per_core;
	uint32_t delay_local_index = ((delay_stage - 1) * n_pre_neurons_per_core) + local_pre_index;
    uint32_t pre_row = delay_core_index + delay_local_index;
    uint32_t idx = pre_row * (max_delayed_row_n_words + N_HEADER_WORDS);
    return (static_row_t *) &delayed_synaptic_matrix[idx];
}

/**
 * \brief Set up the rows so that they are ready for writing to
 * \param[in] matrix The base address of the matrix to set up
 * \param[in] n_rows The number of rows in the matrix
 * \param[in] max_row_n_words The maximum number of words used by a row
 */
static void setup_rows(uint32_t *matrix, uint32_t n_rows, uint32_t max_row_n_words) {
    for (uint32_t i = 0; i < n_rows; i++) {
        static_row_t *row = get_row(matrix, max_row_n_words, i);
        row->plastic_plastic_size = 0;
        row->fixed_plastic_size = 0;
        row->fixed_fixed_size = 0;
    }
}

/**
 * \brief Build a static synaptic word from components
 * \param[in] weight: The weight of the synapse
 * \param[in] delay: The delay of the synapse
 * \param[in] type: The synapse type
 * \param[in] post_index: The core-relative index of the target neuron
 * \param[in] synapse_type_bits: The number of bits for the synapse type
 * \param[in] synapse_index_bits: The number of bits for the target neuron id
 * \param[in] delay_bits: The number of bits for the synaptic delay
 * \return a synaptic word
 */
static uint32_t build_static_word(
        uint16_t weight, uint16_t delay, uint32_t type,
        uint16_t post_index, uint32_t synapse_type_bits,
        uint32_t synapse_index_bits, uint32_t delay_bits) {
    uint32_t synapse_index_mask = (1 << synapse_index_bits) - 1;
    uint32_t synapse_type_mask = (1 << synapse_type_bits) - 1;
    uint32_t synapse_delay_mask = (1 << delay_bits) - 1;

    uint32_t wrd  = post_index & synapse_index_mask;
    wrd |= (type & synapse_type_mask) << synapse_index_bits;
    wrd |= (delay & synapse_delay_mask) <<
            (synapse_index_bits + synapse_type_bits);
    wrd |= (weight & SYNAPSE_WEIGHT_MASK) << SYNAPSE_WEIGHT_SHIFT;
    return wrd;
}

/**
 * \brief How to initialise the static synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \param[in] synaptic_matrix: The address of the base of the synaptic matrix
 * \return A data item to be passed in to other functions later on
 */
static void *matrix_generator_static_initialize(void **region,
        void *synaptic_matrix) {
    matrix_genetator_static_data_t *sdram_data = *region;
    *region = &sdram_data[1];
    matrix_genetator_static_data_t *data = spin1_malloc(
            sizeof(matrix_genetator_static_data_t));
    *data = *sdram_data;

    // Offsets are in words
    uint32_t *syn_mat = synaptic_matrix;
    if (data->synaptic_matrix_offset != 0xFFFFFFFF) {
        data->synaptic_matrix = &(syn_mat[data->synaptic_matrix_offset]);
        setup_rows(data->synaptic_matrix, data->n_pre_neurons,
                data->max_row_n_words);
    } else {
        data->synaptic_matrix = NULL;
    }
    if (data->delayed_matrix_offset != 0xFFFFFFFF) {
        data->delayed_synaptic_matrix = &(syn_mat[data->delayed_matrix_offset]);
        setup_rows(data->delayed_synaptic_matrix,
                data->n_pre_neurons * (data->max_stage - 1),
                data->max_delayed_row_n_words);
    } else {
        data->delayed_synaptic_matrix = NULL;
    }

    return data;
}

/**
 * \brief How to free any data for the static synaptic matrix generator
 * \param[in] generator: The data to free
 */
static void matrix_generator_static_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to write a synapse to a matrix
 * \param[in] generator: The generator data
 * \param[in] pre_index: The index of the pre-neuron relative to the start of
 *                       the matrix
 * \param[in] post_index: The index of the post-neuron on this core
 * \param[in] weight: The weight of the synapse in raw format
 * \param[in] delay: The delay of the synapse in time steps
 * \param[in] weight_scale: The scale to apply to the weight if needed
 * \return whether the synapses was added or not
 */
static bool matrix_generator_static_write_synapse(void *generator,
        uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay,
		accum weight_scale) {
    matrix_genetator_static_data_t *data = generator;
    struct delay_value delay_and_stage = get_delay(delay, data->max_stage,
            data->max_delay_per_stage);
    static_row_t *row;
    uint32_t pos;
    if (delay_and_stage.stage == 0) {
        row = get_row(data->synaptic_matrix, data->max_row_n_words, pre_index);
        pos = row->fixed_fixed_size;
        if (pos >= data->max_row_n_words) {
            log_warning("Row %u at 0x%08x of matrix 0x%08x is already full (%u of %u)",
                    pre_index, row, data->synaptic_matrix, pos, data->max_row_n_words);
            return false;
        }
    } else {
        row = get_delay_row(data->delayed_synaptic_matrix,
                data->max_delayed_row_n_words, pre_index, delay_and_stage.stage,
                data->n_pre_neurons_per_core, data->max_stage);
        log_info("Writing pre_index %u with delay %u (%u), stage %u to row 0x%08x",
                pre_index, delay, delay_and_stage.delay, delay_and_stage.stage, row);
        pos = row->fixed_fixed_size;
        if (pos >= data->max_delayed_row_n_words) {
            log_warning("Row %u, stage %u at 0x%08x of delayed matrix 0x%08x"
            		"is already full (%u of %u)",
                    pre_index, delay_and_stage.stage, row,
					data->delayed_synaptic_matrix, pos, data->max_delayed_row_n_words);
            return false;
        }
    }

    uint16_t scaled_weight = rescale_weight(weight, weight_scale);

    row->fixed_fixed_size = pos + 1;
    row->fixed_fixed_data[pos] = build_static_word(scaled_weight, delay_and_stage.delay,
            data->synapse_type, post_index, data->synapse_type_bits,
            data->synapse_index_bits, data->delay_bits);
    return true;
}
