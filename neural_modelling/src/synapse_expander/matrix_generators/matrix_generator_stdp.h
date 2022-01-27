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
} *row_plastic_t;

//! The layout of the fixed synapse region of the row; the fixed-fixed region is empty
typedef struct {
    uint32_t fixed_fixed_size;      //!< the fixed-fixed size within the fixed region
    uint32_t fixed_plastic_size;    //!< the fixed-plastic size within the fixed region
    uint16_t fixed_plastic_data[];  //!< the fixed-plastic data within the fixed region
} *row_fixed_t;

//! Data for the generator
struct matrix_generator_stdp {
    //! The number of half-words in a plastic-plastic row header
    uint32_t n_half_words_per_pp_row_header;
    //! The number of half-words in each plastic-plastic synapse
    uint32_t n_half_words_per_pp_synapse;
    //! The index of the half-word that will contain the weight
    uint32_t weight_half_word;
};

/**
 * \brief Initialise the STDP synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
void *matrix_generator_stdp_initialize(void **region) {
    // Allocate memory for the parameters
    struct matrix_generator_stdp *obj =
            spin1_malloc(sizeof(struct matrix_generator_stdp));

    // Copy the parameters in
    struct matrix_generator_stdp *params_sdram = *region;
    *obj = *params_sdram;
    *region = &params_sdram[1];
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
 * \brief Generate a row of a STDP synaptic matrix
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
 * \param[in] max_delay_per_stage: the max delay per delay stage
 */
void matrix_generator_stdp_write_row(
        void *generator,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage, uint32_t max_delay_per_stage) {
    struct matrix_generator_stdp *obj = generator;

    // Row address for each possible delay stage (including no delay stage)
    row_plastic_t row[max_stage];

    // Space available in each row
    uint16_t space_half_words[max_stage];

    // The number of words in a row including headers
    uint32_t n_row_words = max_row_n_words + 3;
    uint32_t n_delay_row_words = max_delayed_row_n_words + 3;

    // The normal row position and space available - might be 0 if all delayed
    row[0] = NULL;
    space_half_words[0] = max_row_n_words * 2;
    if (synaptic_matrix != NULL) {
        row[0] = (row_plastic_t)
                &synaptic_matrix[pre_neuron_index * n_row_words];
    }

    // The delayed row positions and space available
    if (delayed_synaptic_matrix != NULL) {
        address_t delayed_address =
                &delayed_synaptic_matrix[pre_neuron_index * n_delay_row_words];
        uint32_t single_matrix_size = n_pre_neurons * n_delay_row_words;
        for (uint32_t i = 1; i < max_stage; i++) {
            row[i] = (row_plastic_t)
                    &delayed_address[single_matrix_size * (i - 1)];
            space_half_words[i] = max_delayed_row_n_words * 2;
        }
    } else {
        for (uint32_t i = 1; i < max_stage; i++) {
            row[i] = NULL;
            space_half_words[i] = 0;
        }
    }

    // Add the header half words (zero initialised) to each row
    for (uint32_t i = 0; i < max_stage; i++) {
        if (row[i] != NULL) {
            row[i]->plastic_plastic_size =
                    obj->n_half_words_per_pp_row_header >> 1;
            uint16_t *header = row[i]->plastic_plastic_data;
            for (uint32_t j = 0;
                    j < obj->n_half_words_per_pp_row_header; j++) {
                header[j] = 0;
            }
            space_half_words[i] -= obj->n_half_words_per_pp_row_header;
        }
    }

    // Get the plastic-plastic position at the start of each row and keep track
    // of the number of half-words per row (to allow padding later)
    uint16_t *pp_address[max_stage];
    uint16_t n_half_words_per_row[max_stage];
    for (uint32_t i = 0; i < max_stage; i++) {
        n_half_words_per_row[i] = 0;
        if (row[i] != NULL) {
            pp_address[i] = &row[i]->plastic_plastic_data[
                    obj->n_half_words_per_pp_row_header];
        } else {
            pp_address[i] = NULL;
        }
    }

    // Write the plastic-plastic part of the row
    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {
        // Weight
        uint16_t weight = weights[synapse];
        // Delay (mostly to get the stage)
        struct delay_value delay = get_delay(
            delays[synapse], max_stage, max_delay_per_stage);

        // Check that the position is valid
        if (delay.stage >= max_stage || pp_address[delay.stage] == NULL) {
            log_error("Delay stage %u has not been initialised", delay.stage);
            rt_error(RTE_SWERR);
        }

        // Check there is enough space
        if (space_half_words[delay.stage] < obj->n_half_words_per_pp_synapse) {
            log_warning("Row %u only has %u half words of %u free - not writing",
                    delay.stage, space_half_words[delay.stage],
                    obj->n_half_words_per_pp_synapse);
            continue;
        }

        // Put the weight words in place
        uint16_t *weight_words = pp_address[delay.stage];
        pp_address[delay.stage] =
                &pp_address[delay.stage][obj->n_half_words_per_pp_synapse];
        for (uint32_t i = 0; i < obj->n_half_words_per_pp_synapse; i++) {
            weight_words[i] = 0;
        }
        weight_words[obj->weight_half_word] = weight;
        n_half_words_per_row[delay.stage] += obj->n_half_words_per_pp_synapse;
        space_half_words[delay.stage] -= obj->n_half_words_per_pp_synapse;
    }

    // Add padding to any rows that are not word-aligned
    // and set the size in words
    for (uint32_t i = 0; i < max_stage; i++) {
        if (row[i] != NULL) {
            if (n_half_words_per_row[i] & 0x1) {
                *pp_address[i]++ = 0;
                n_half_words_per_row[i]++;
            }
            row[i]->plastic_plastic_size += n_half_words_per_row[i] >> 1;
        }
    }

    // PP address is now fixed region address
    // Set the fixed-fixed size to 0 and point to the fixed-plastic region
    row_fixed_t fixed[max_stage];
    uint16_t *fp_address[max_stage];
    for (uint32_t i = 0; i < max_stage; i++) {
        fixed[i] = (row_fixed_t) pp_address[i];
        if (fixed[i] != NULL) {
            fp_address[i] = fixed[i]->fixed_plastic_data;
            fixed[i]->fixed_fixed_size = 0;
            fixed[i]->fixed_plastic_size = 0;
        } else {
            fp_address[i] = NULL;
        }
    }

    uint32_t max_delay_power_2 = max_delay_per_stage;
    uint32_t log_max_delay = 1;
    if (max_delay_power_2 != 1) {
        if (!is_power_of_2(max_delay_power_2)) {
            max_delay_power_2 = next_power_of_2(max_delay_power_2);
        }
        log_max_delay = ilog_2(max_delay_power_2);
    }

    // Write the fixed-plastic part of the row
    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {
        // Post-neuron index
        uint32_t post_index = indices[synapse];

        struct delay_value delay = get_delay(
            delays[synapse], max_stage, max_delay_per_stage);

        // Build synaptic word
        uint16_t fp_half_word = build_fixed_plastic_half_word(
                delay.delay, synapse_type, post_index, synapse_type_bits,
                synapse_index_bits, log_max_delay);

        // Write the half-word
        *fp_address[delay.stage]++ = fp_half_word;

        // Increment the size of the current row
        fixed[delay.stage]->fixed_plastic_size++;
    }
}
