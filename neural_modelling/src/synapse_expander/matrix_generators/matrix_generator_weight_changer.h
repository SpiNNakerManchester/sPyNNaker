/*
 * Copyright (c) 2024 The University of Manchester
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
 * \brief Weight-changer synaptic matrix implementation
 */

#include <stdbool.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include "matrix_generator_common.h"
#include <synapse_expander/generator_types.h>
#include <utils.h>

typedef struct {
    union {
        //! The address of the synaptic matrix (once initialised)
        uint32_t *synaptic_matrix;
        //! The offset of the synaptic matrix (as read from SDRAM)
        uint32_t synaptic_matrix_offset;
    };
    uint32_t max_row_n_words;
    uint32_t max_row_n_synapses;
    uint32_t n_pre_neurons;
    uint32_t synapse_type;
    uint32_t synapse_type_bits;
    uint32_t synapse_index_bits;
    uint32_t row_offset;
} matrix_generator_weight_changer;

//! The layout of the initial plastic synapse part of the row
typedef struct {
    uint32_t plastic_plastic_size;   //!< the plastic-plastic size within the row
    uint32_t pre_spike: 31;
    uint32_t is_update: 1;
} row_changer_plastic_t;

//! The layout of the fixed synapse region of the row; the fixed-fixed region is empty
typedef struct {
    uint32_t fixed_fixed_size;      //!< the fixed-fixed size within the fixed region
    uint32_t fixed_plastic_size;    //!< the fixed-plastic size within the fixed region
    int32_t fixed_plastic_data[];  //!< the fixed-plastic data within the fixed region
} row_changer_fixed_t;

/**
 * \brief Get a synaptic row for a given neuron
 * \param[in] synaptic_matrix the address of the synaptic matrix
 * \param[in] max_row_n_words the maximum number of words (excluding headers)
 *                            in each row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \return A pointer to the row of the matrix to write to
 */
static row_changer_plastic_t *get_changer_row(uint32_t *synaptic_matrix,
		uint32_t max_row_n_words, uint32_t pre_index) {
    uint32_t idx = pre_index * (max_row_n_words + N_HEADER_WORDS);
    return (row_changer_plastic_t *) &synaptic_matrix[idx];
}

/**
 * \brief Get the fixed part of a row that comes after the plastic part.
 * \param[in] plastic_row A pointer to the row to find the fixed part of
 * \return A pointer to the fixed part of the matrix to write to
 */
static row_changer_fixed_t *get_changer_fixed_row(row_changer_plastic_t *plastic_row) {
    return (row_changer_fixed_t *) &plastic_row[1];
}

/**
 * \brief Set up the rows so that they are ready for writing to
 * \param[in] matrix The base address of the matrix to set up
 * \param[in] n_rows The number of rows in the matrix
 * \param[in] max_row_n_words The maximum number of words used by a row
 */
static void setup_changer_rows(uint32_t *matrix, uint32_t n_rows,
		uint32_t max_row_n_words, uint32_t row_offset) {
    for (uint32_t i = 0; i < n_rows; i++) {
        row_changer_plastic_t *row = get_changer_row(matrix, max_row_n_words, i);
        row->plastic_plastic_size = 1;
        row->pre_spike = i + row_offset;
        row->is_update = 1;
        row_changer_fixed_t *fixed = get_changer_fixed_row(row);
        fixed->fixed_fixed_size = 0;
        fixed->fixed_plastic_size = 0;
    }
}


/**
 * \brief Initialise the Changer synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \param[in] synaptic_matrix: The base address of the synaptic matrix
 * \return A data item to be passed in to other functions later on
 */
void *matrix_generator_changer_initialize(void **region,
        void *synaptic_matrix) {
    // Allocate memory for the parameters
    matrix_generator_weight_changer *conf =
            spin1_malloc(sizeof(matrix_generator_weight_changer));

    // Copy the parameters in
    matrix_generator_weight_changer *params_sdram = *region;
    *conf = *params_sdram;
    *region = &params_sdram[1];

    // Offsets are in words
    uint32_t *syn_mat = synaptic_matrix;
    conf->synaptic_matrix = &(syn_mat[conf->synaptic_matrix_offset]);
    setup_changer_rows(conf->synaptic_matrix, conf->n_pre_neurons,
    		conf->max_row_n_words, conf->row_offset);

    return conf;
}

/**
 * \brief Free any data for the matrix generator
 * \param[in] generator: The generator to free
 */
void matrix_generator_changer_free(void *generator) {
    sark_free(generator);
}

static uint32_t build_changer_word(
        uint32_t type, uint32_t post_index, uint32_t synapse_type_bits,
        uint32_t synapse_index_bits, int16_t weight) {
    uint32_t synapse_index_mask = (1 << synapse_index_bits) - 1;
    uint32_t synapse_type_mask = (1 << synapse_type_bits) - 1;

    uint32_t wrd = post_index & synapse_index_mask;
    wrd |= (type & synapse_type_mask) << synapse_index_bits;
    // The weight position is fixed
    wrd |= weight << 16;

    return wrd;
}

static bool matrix_generator_changer_write_synapse(void *generator,
        uint32_t pre_index, uint16_t post_index, accum weight,
        UNUSED uint16_t delay, unsigned long accum weight_scale) {
    matrix_generator_weight_changer *conf = generator;
    row_changer_plastic_t *plastic_row = get_changer_row(conf->synaptic_matrix,
            conf->max_row_n_words, pre_index);
    row_changer_fixed_t *fixed_row = get_changer_fixed_row(plastic_row);
    uint32_t pos = fixed_row->fixed_plastic_size;
    if (pos >= conf->max_row_n_synapses) {
        log_warning("Row %u at 0x%08x, 0x%08x of matrix 0x%08x is already full (%u of %u)",
                pre_index, plastic_row, fixed_row, conf->synaptic_matrix, pos,
				conf->max_row_n_synapses);
        return false;
    }
    uint16_t scaled_weight = rescale_weight(weight, weight_scale);
    int16_t signed_weight = (int16_t) scaled_weight;
    if (weight < 0) {
        signed_weight = -signed_weight;
    }
    fixed_row->fixed_plastic_size = pos + 1;
	fixed_row->fixed_plastic_data[pos] = build_changer_word(conf->synapse_type,
			post_index, conf->synapse_type_bits, conf->synapse_index_bits,
			signed_weight);
    return true;
}
