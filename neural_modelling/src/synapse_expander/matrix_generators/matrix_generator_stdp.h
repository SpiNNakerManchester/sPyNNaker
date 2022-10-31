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
 * \brief STDP synaptic matrix implementation
 */


#include <stdbool.h>
#include <spin1_api.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include "matrix_generator_common.h"
#include <synapse_expander/generator_types.h>
#include <utils.h>

//! The layout of the initial plastic synapse part of the row
typedef struct {
    uint32_t plastic_plastic_size;   //!< the plastic-plastic size within the row
    uint16_t plastic_plastic_data[]; //!< the plastic-plastic data within the row
} row_plastic_t;

//! The layout of the fixed synapse region of the row; the fixed-fixed region is empty
typedef struct {
    uint32_t fixed_fixed_size;      //!< the fixed-fixed size within the fixed region
    uint32_t fixed_plastic_size;    //!< the fixed-plastic size within the fixed region
    uint16_t fixed_plastic_data[];  //!< the fixed-plastic data within the fixed region
} row_fixed_t;

//! Data for the generator
typedef struct matrix_generator_stdp {
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
    //! The maximum number of synapses on a row
    uint32_t max_row_n_synapses;
    //! The maximum number of synapses on a delayed row
    uint32_t max_delayed_row_n_synapses;
    //! The maximum number of words on a row
    uint32_t max_row_n_words;
    //! The maximum number of words on a delayed row
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
    //! The number of half-words in a plastic-plastic row header
    uint32_t n_half_words_per_pp_row_header;
    //! The number of half-words in each plastic-plastic synapse
    uint32_t n_half_words_per_pp_synapse;
    //! The index of the half-word that will contain the weight
    uint32_t weight_half_word;
} matrix_generator_stdp_data_t;

/**
 * \brief Get a synaptic row for a given neuron
 * \param[in] synaptic_matrix the address of the synaptic matrix
 * \param[in] max_row_n_words the maximum number of words (excluding headers)
 *                            in each row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \return A pointer to the row of the matrix to write to
 */
static row_plastic_t *get_stdp_row(uint32_t *synaptic_matrix, uint32_t max_row_n_words,
        uint32_t pre_index) {
    uint32_t idx = pre_index * (max_row_n_words + N_HEADER_WORDS);
    return (row_plastic_t *) &synaptic_matrix[idx];
}

/**
 * \brief Get a delayed synaptic row for a given neuron and delay stage
 * \param[in] delayed synaptic_matrix the address of the delayed synaptic matrix
 * \param[in] max_delayed_row_n_words the maximum number of words (excluding headers)
 *                                    in each delayed row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \param[in] delay_stage the delay stage, where 0 means the first stage
 * \param[in] n_pre_neurons_per_core The number of neurons per core in the pre-population
 * \param[in] max_delay_stage The maximum delay stage
 * \return A pointer to the row of the delayed matrix to write to
 */
static row_plastic_t *get_stdp_delay_row(uint32_t *delayed_synaptic_matrix,
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
	return (row_plastic_t *) &delayed_synaptic_matrix[idx];
}

/**
 * \brief Get the maximum number of plastic half-words in a row
 * \param[in] n_half_words_per_pp_header the number of half-words at the start
 *                                       of each row
 * \param[in] n_half_words_per_pp_synapse the number of half-words used by each
 *                                        synapse
 * \param[in] max_row_n_synapses the maximum number of synapses in a row
 * \return the number of plastic half-words in a maximum length row
 */
static uint32_t plastic_half_words(uint32_t n_half_words_per_pp_header,
        uint32_t n_half_words_per_pp_synapse, uint32_t max_row_n_synapses) {
    uint32_t n_half_words = n_half_words_per_pp_header
            + (n_half_words_per_pp_synapse * max_row_n_synapses);
    if (n_half_words & 0x1) {
        n_half_words += 1;
    }
    return n_half_words;
}

/**
 * \brief Get the fixed part of a row that comes after the plastic part.  Note
 *        that this assumes the max row size in number of synapses.
 * \param[in] plastic_row A pointer to the row to find the fixed part of
 * \param[in] n_half_words_per_pp_header the (even) number of header words at the
 *                                       start of the plastic data
 * \param[in] n_half_words_per_pp_synapse the number of half-words in each synapse,
 *                                        not necessarily even
 * \param[in] max_row_n_synapses the maximum number of synapses in the row
 * \return A pointer to the fixed part of the row assuming all synapses used
 */
static row_fixed_t *get_stdp_fixed_row(row_plastic_t *plastic_row,
        uint32_t n_half_words_per_pp_header, uint32_t n_half_words_per_pp_synapse,
        uint32_t max_row_n_synapses) {
    uint32_t idx_16 = plastic_half_words(n_half_words_per_pp_header,
            n_half_words_per_pp_synapse, max_row_n_synapses);
    return (row_fixed_t *) &(plastic_row->plastic_plastic_data[idx_16]);
}

/**
 * \brief Set up the rows so that they are ready for writing to
 * \param[in] matrix The base address of the matrix to set up
 * \param[in] n_rows The number of rows in the matrix
 * \param[in] n_half_words_per_pp_header The number of half-words at the start
 *                                       of each row
 * \param[in] n_half_words_per_pp_synapse The number of half-words used by each
 *                                        synapse
 * \param[in] max_row_n_synapses The maximum number of synapses in a row
 * \param[in] max_row_n_words The maximum number of words used by a row
 */
static void setup_stdp_rows(uint32_t *matrix, uint32_t n_rows,
        uint32_t n_half_words_per_pp_header, uint32_t n_half_words_per_pp_synapse,
        uint32_t max_row_n_synapses, uint32_t max_row_n_words) {

    // Set all the header half-words to 0 and set all the sizes
    uint32_t plastic_words = plastic_half_words(n_half_words_per_pp_header,
            n_half_words_per_pp_synapse, max_row_n_synapses) >> 1;
    for (uint32_t i = 0; i < n_rows; i++) {
        row_plastic_t *row = get_stdp_row(matrix, max_row_n_words, i);
        // Use word writing for efficiency
        uint32_t *data = (uint32_t *) &row->plastic_plastic_data[0];
        for (uint32_t j = 0; j < plastic_words; j++) {
            data[j] = 0;
        }
        row->plastic_plastic_size = plastic_words;
        row_fixed_t *fixed = get_stdp_fixed_row(row, n_half_words_per_pp_header,
                n_half_words_per_pp_synapse, max_row_n_synapses);
        fixed->fixed_fixed_size = 0;
        fixed->fixed_plastic_size = 0;
    }
}


/**
 * \brief Build a fixed-plastic half-word from its components
 * \param[in] delay: The delay of the synapse
 * \param[in] type: The synapse type
 * \param[in] post_index: The core-relative index of the target neuron
 * \param[in] synapse_type_bits: The number of bits for the synapse type
 * \param[in] synapse_index_bits: The number of bits for the target neuron id
 * \param[in] delay_bits: The number of bits for the synaptic delay
 * \return A half-word fixed-plastic synapse
 */
static uint16_t build_fixed_plastic_half_word(
        uint16_t delay, uint32_t type,
        uint32_t post_index, uint32_t synapse_type_bits,
        uint32_t synapse_index_bits, uint32_t delay_bits) {
    uint16_t synapse_index_mask = (1 << synapse_index_bits) - 1;
    uint16_t synapse_type_mask = (1 << synapse_type_bits) - 1;
    uint16_t delay_mask = (1 << delay_bits) - 1;

    uint16_t wrd = post_index & synapse_index_mask;
    wrd |= (type & synapse_type_mask) << synapse_index_bits;
    wrd |= (delay & delay_mask) <<
            (synapse_index_bits + synapse_type_bits);
    // wrd |= (delay & SYNAPSE_DELAY_MASK) << synapse_type_bits;

    return wrd;
}

/**
 * \brief Initialise the STDP synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \param[in] synaptic_matrix: The base address of the synaptic matrix
 * \return A data item to be passed in to other functions later on
 */
void *matrix_generator_stdp_initialize(void **region, void *synaptic_matrix) {
    // Allocate memory for the parameters
    matrix_generator_stdp_data_t *obj =
            spin1_malloc(sizeof(matrix_generator_stdp_data_t));

    // Copy the parameters in
    matrix_generator_stdp_data_t *params_sdram = *region;
    *obj = *params_sdram;
    *region = &params_sdram[1];

    // Offsets are in words
    uint32_t *syn_mat = synaptic_matrix;
    if (obj->synaptic_matrix_offset != 0xFFFFFFFF) {
        obj->synaptic_matrix = &(syn_mat[obj->synaptic_matrix_offset]);
        setup_stdp_rows(obj->synaptic_matrix, obj->n_pre_neurons,
                obj->n_half_words_per_pp_row_header,
                obj->n_half_words_per_pp_synapse, obj->max_row_n_synapses,
                obj->max_row_n_words);
    } else {
        obj->synaptic_matrix = NULL;
    }

    if (obj->delayed_matrix_offset != 0xFFFFFFFF) {
        obj->delayed_synaptic_matrix = &(syn_mat[obj->delayed_matrix_offset]);
        setup_stdp_rows(obj->delayed_synaptic_matrix,
                obj->n_pre_neurons * (obj->max_stage - 1),
                obj->n_half_words_per_pp_row_header,
                obj->n_half_words_per_pp_synapse,
                obj->max_delayed_row_n_synapses, obj->max_delayed_row_n_words);
    } else {
        obj->delayed_synaptic_matrix = NULL;
    }

    return obj;
}

/**
 * \brief Free any data for the STDP synaptic matrix generator
 * \param[in] generator: The generator to free
 */
void matrix_generator_stdp_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief How to write a synapse to a matrix
 * \param[in] generator: The generator data
 * \param[in] pre_index: The index of the pre-neuron relative to the start of
 *                       the matrix
 * \param[in] post_index: The index of the post-neuron on this core
 * \param[in] weight: The weight of the synapse in raw form
 * \param[in] delay: The delay of the synapse in time steps
 * \param[in] weight_scale: The scale to apply to the weight if needed
 */
static bool matrix_generator_stdp_write_synapse(void *generator,
        uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay,
		unsigned long accum weight_scale) {
    matrix_generator_stdp_data_t *data = generator;
    struct delay_value delay_and_stage = get_delay(delay, data->max_stage,
            data->max_delay_per_stage);
    row_plastic_t *plastic_row;
    row_fixed_t *fixed_row;
    uint32_t pos;
    if (delay_and_stage.stage == 0) {
        plastic_row = get_stdp_row(data->synaptic_matrix, data->max_row_n_words,
                pre_index);
        fixed_row = get_stdp_fixed_row(plastic_row,
                data->n_half_words_per_pp_row_header,
                data->n_half_words_per_pp_synapse, data->max_row_n_synapses);
        pos = fixed_row->fixed_plastic_size;
        if (pos >= data->max_row_n_synapses) {
            log_warning("Row %u at 0x%08x, 0x%08x of matrix 0x%08x is already full (%u of %u)",
                pre_index, plastic_row, fixed_row, data->synaptic_matrix, pos,
				data->max_row_n_synapses);
            return false;
        }
    } else {
        plastic_row = get_stdp_delay_row(data->delayed_synaptic_matrix,
                data->max_delayed_row_n_words, pre_index, delay_and_stage.stage,
                data->n_pre_neurons_per_core, data->max_stage);
        fixed_row = get_stdp_fixed_row(plastic_row,
                data->n_half_words_per_pp_row_header,
                data->n_half_words_per_pp_synapse, data->max_delayed_row_n_synapses);
        pos = fixed_row->fixed_plastic_size;
        if (pos >= data->max_delayed_row_n_synapses) {
            log_warning("Row %u at 0x%08x, 0x%08x of matrix 0x%08x is already full (%u of %u)",
                pre_index, plastic_row, fixed_row, data->synaptic_matrix, pos,
				data->max_delayed_row_n_synapses);
            return false;
        }
    }

    uint16_t scaled_weight = rescale_weight(weight, weight_scale);

    fixed_row->fixed_plastic_size = pos + 1;
    fixed_row->fixed_plastic_data[pos] = build_fixed_plastic_half_word(
            delay_and_stage.delay, data->synapse_type, post_index,
            data->synapse_type_bits, data->synapse_index_bits, data->delay_bits);
    uint32_t plastic_pos = data->n_half_words_per_pp_row_header
            + (data->n_half_words_per_pp_synapse * pos) + data->weight_half_word;
    plastic_row->plastic_plastic_data[plastic_pos] = scaled_weight;
    return true;
}
