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

/**
 * \brief How to generate a row of a static synaptic matrix
 * \param[in] generator:
 *      The data for the matrix generator, returned by the initialise function
 * \param[out] synaptic_matrix: The address of the synaptic matrix to write to
 * \param[out] delayed_synaptic_matrix:
 *      The address of the synaptic matrix to write delayed connections to
 * \param[in] n_pre_neurons: The number of pre neurons to generate for
 * \param[in] pre_neuron_index: The index of the first pre neuron
 * \param[in] max_row_n_words: The maximum number of words in a normal row
 * \param[in] max_delayed_row_n_words:
 *      The maximum number of words in a delayed row
 * \param[in] synapse_type_bits: The number of bits used for the synapse type
 * \param[in] synapse_index_bits: The number of bits used for the neuron id
 * \param[in] synapse_type: The synapse type of each connection
 * \param[in] n_synapses: The number of synapses
 * \param[in] indices: Pointer to table of indices
 * \param[in] delays: Pointer to table of delays
 * \param[in] weights: Pointer to table of weights
 * \param[in] max_stage: The maximum delay stage to support
 * \param[in] max_delay_per_stage: The max delay per delay stage
 */

#include <stdbool.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include "matrix_generator_common.h"
#include <synapse_expander/generator_types.h>
#include <utils.h>

typedef struct {
    uint32_t reward_synapse_type;
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
 * \brief Initialise the Neuromodulation synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
void *matrix_generator_neuromodulation_initialize(address_t *region) {
    // Allocate memory for the parameters
    matrix_generator_neuromodulation *conf =
            spin1_malloc(sizeof(matrix_generator_neuromodulation));

    // Copy the parameters in
    matrix_generator_neuromodulation *params_sdram = (void *) *region;
    *conf = *params_sdram++;
    *region = (void *) params_sdram;
    return conf;
}

/**
 * \brief Free any data for the STDP synaptic matrix generator
 * \param[in] generator: The generator to free
 */
void matrix_generator_neuromodulation_free(void *generator) {
    sark_free(generator);
}

static void matrix_generator_neuromodulation_write_row(
        void *generator,
        address_t synaptic_matrix, UNUSED address_t delayed_synaptic_matrix,
        UNUSED uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, UNUSED uint32_t max_delayed_row_n_words,
        UNUSED uint32_t synapse_type_bits, UNUSED uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses, uint16_t *indices,
        UNUSED uint16_t *delays, uint16_t *weights, UNUSED uint32_t max_stage,
        UNUSED uint32_t max_delay_per_stage) {

    matrix_generator_neuromodulation *conf = generator;

    // The number of words in a row including headers
    uint32_t n_row_words = max_row_n_words + 3;

    // The normal row position
    row_nm_plastic_t *row =
            (row_nm_plastic_t *) &synaptic_matrix[pre_neuron_index * n_row_words];
    row->plastic_plastic_size = 1;
    row->is_neuromodulation = 1;
    row->is_reward = synapse_type == conf->reward_synapse_type;
    row->synapse_type = synapse_type;

    // Set the fixed-fixed size to 0 and point to the fixed-plastic region
    row_nm_fixed_t *fixed = (row_nm_fixed_t *) &row[1];
    fixed->fixed_fixed_size = 0;
    fixed->fixed_plastic_size = n_synapses;

    // Go through the synapses
    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {
        // Post-neuron index
        uint32_t post_index = indices[synapse];

        // Weight
        uint16_t weight = weights[synapse];

        fixed->fixed_plastic_data[synapse] = (weight << 16) | post_index;
    }
}
