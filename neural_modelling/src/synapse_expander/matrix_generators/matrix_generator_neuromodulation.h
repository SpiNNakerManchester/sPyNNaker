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
 * \brief Neuromodulation synaptic matrix implementation
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
    uint32_t is_reward;
    uint32_t synapse_type;
} matrix_generator_neuromodulation;

//! The layout of the initial plastic synapse part of the row
typedef struct {
    uint32_t plastic_plastic_size;   //!< the plastic-plastic size within the row
    uint32_t is_neuromodulation:1;   //!< is the row neuromodulation
    uint32_t is_reward:1;            //!< is the row reward
    uint32_t synapse_type:30;        //!< the synapse type of the row
} row_nm_plastic_t;

//! The layout of the fixed synapse region of the row; the fixed-fixed region is empty
typedef struct {
    uint32_t fixed_fixed_size;      //!< the fixed-fixed size within the fixed region
    uint32_t fixed_plastic_size;    //!< the fixed-plastic size within the fixed region
    uint32_t fixed_plastic_data[];  //!< the fixed-plastic data within the fixed region
} row_nm_fixed_t;

/**
 * \brief Get a synaptic row for a given neuron
 * \param[in] synaptic_matrix the address of the synaptic matrix
 * \param[in] max_row_n_words the maximum number of words (excluding headers)
 *                            in each row of the table
 * \param[in] pre_index the index of the pre-neuron relative to the start of the
 *                      matrix
 * \return A pointer to the row of the matrix to write to
 */
static row_nm_plastic_t *get_nm_row(uint32_t *synaptic_matrix, uint32_t max_row_n_words,
        uint32_t pre_index) {
    uint32_t idx = pre_index * (max_row_n_words + N_HEADER_WORDS);
    return (row_nm_plastic_t *) &synaptic_matrix[idx];
}

/**
 * \brief Get the fixed part of a row that comes after the plastic part.
 * \param[in] plastic_row A pointer to the row to find the fixed part of
 * \return A pointer to the fixed part of the matrix to write to
 */
static row_nm_fixed_t *get_nm_fixed_row(row_nm_plastic_t *plastic_row) {
    return (row_nm_fixed_t *) &plastic_row[1];
}

/**
 * \brief Set up the rows so that they are ready for writing to
 * \param[in] matrix The base address of the matrix to set up
 * \param[in] n_rows The number of rows in the matrix
 * \param[in] max_row_n_words The maximum number of words used by a row
 */
static void setup_nm_rows(uint32_t *matrix, uint32_t n_rows, uint32_t max_row_n_words,
        uint32_t is_reward, uint32_t synapse_type) {
    // Set all the header half-words to 0 and set all the sizes
    for (uint32_t i = 0; i < n_rows; i++) {
        row_nm_plastic_t *row = get_nm_row(matrix, max_row_n_words, i);
        row->plastic_plastic_size = 1;
        row->is_neuromodulation = 1;
        row->is_reward = is_reward;
        row->synapse_type = synapse_type;
        row_nm_fixed_t *fixed = get_nm_fixed_row(row);
        fixed->fixed_fixed_size = 0;
        fixed->fixed_plastic_size = 0;
    }
}


/**
 * \brief Initialise the Neuromodulation synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \param[in] synaptic_matrix: The base address of the synaptic matrix
 * \return A data item to be passed in to other functions later on
 */
void *matrix_generator_neuromodulation_initialize(void **region,
        void *synaptic_matrix) {
    // Allocate memory for the parameters
    matrix_generator_neuromodulation *conf =
            spin1_malloc(sizeof(matrix_generator_neuromodulation));

    // Copy the parameters in
    matrix_generator_neuromodulation *params_sdram = *region;
    *conf = *params_sdram;
    *region = &params_sdram[1];

    // Offsets are in words
    uint32_t *syn_mat = synaptic_matrix;
    conf->synaptic_matrix = &(syn_mat[conf->synaptic_matrix_offset]);
    setup_nm_rows(conf->synaptic_matrix, conf->n_pre_neurons, conf->max_row_n_words,
            conf->is_reward, conf->synapse_type);

    return conf;
}

/**
 * \brief Free any data for the STDP synaptic matrix generator
 * \param[in] generator: The generator to free
 */
void matrix_generator_neuromodulation_free(void *generator) {
    sark_free(generator);
}

static bool matrix_generator_neuromodulation_write_synapse(void *generator,
        uint32_t pre_index, uint16_t post_index, uint16_t weight,
        UNUSED uint16_t delay) {
    matrix_generator_neuromodulation *conf = generator;
    row_nm_plastic_t *plastic_row = get_nm_row(conf->synaptic_matrix,
            conf->max_row_n_words, pre_index);
    row_nm_fixed_t *fixed_row = get_nm_fixed_row(plastic_row);
    uint32_t pos = fixed_row->fixed_plastic_size;
    if (pos >= conf->max_row_n_synapses) {
        log_warning("Row %u at 0x%08x, 0x%08x of matrix 0x%08x is already full (%u of %u)",
                pre_index, plastic_row, fixed_row, conf->synaptic_matrix, pos,
				conf->max_row_n_synapses);
        return false;
    }
    fixed_row->fixed_plastic_size = pos + 1;
    fixed_row->fixed_plastic_data[pos] = (weight << 16) | post_index;
    return true;
}
