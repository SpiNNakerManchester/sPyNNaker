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

/**
 * \brief How to initialise the static synaptic matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *matrix_generator_static_initialize(UNUSED address_t *region) {
    return NULL;
}

/**
 * \brief How to free any data for the static synaptic matrix generator
 * \param[in] generator: The data to free
 */
static void matrix_generator_static_free(UNUSED void *generator) {
}

/**
 * \brief The shift of the weight within a synaptic word
 */
#define SYNAPSE_WEIGHT_SHIFT 16

/**
 * \brief The mask of a weight before shifting
 */
#define SYNAPSE_WEIGHT_MASK 0xFFFF

//! The layout of a purely static row of a synaptic matrix.
typedef struct {
    uint32_t plastic_plastic_size;  //!< the plastic-plastic size within a row
    uint32_t fixed_fixed_size;      //!< the fixed-fixed size within a row
    uint32_t fixed_plastic_size;    //!< the fixed-plastic size within a row
    uint32_t fixed_fixed_data[];    //!< the fixed-fixed data within a row
} *static_row_t;

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
static void matrix_generator_static_write_row(
        UNUSED void *generator,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage, uint32_t max_delay_per_stage) {
    log_debug("Max stage = %u", max_stage);

    // Row address and position for each possible delay stage (including no
    // delay stage)
    static_row_t row[max_stage];

    // The space available on each row
    uint16_t space[max_stage];

    // The normal row position and space available - might be 0 if all delayed
    row[0] = NULL;
    space[0] = max_row_n_words;
    if (synaptic_matrix != NULL) {
        row[0] = (static_row_t)
                &synaptic_matrix[pre_neuron_index * (max_row_n_words + 3)];
    }
    log_debug("row[0] = 0x%08x", row[0]);

    // The delayed row positions and space available
    if (delayed_synaptic_matrix != NULL) {
        address_t delayed_address = &delayed_synaptic_matrix[
                pre_neuron_index * (max_delayed_row_n_words + 3)];
        uint32_t single_matrix_size =
                n_pre_neurons * (max_delayed_row_n_words + 3);
        for (uint32_t i = 1; i < max_stage; i++) {
            row[i] = (static_row_t)
                    &delayed_address[single_matrix_size * (i - 1)];
            space[i] = max_delayed_row_n_words;
            log_debug("row[%u] = 0x%08x", i, row[i]);
        }
    } else {
        for (uint32_t i = 1; i < max_stage; i++) {
            row[i] = NULL;
            space[i] = 0;
            log_debug("row[%u] = 0x%08x", i, row[i]);
        }
    }

    // The address to write synapses to on each stage
    address_t write_address[max_stage];
    for (uint32_t i = 0; i < max_stage; i++) {
        if (row[i] != NULL) {
            log_debug("Row size at 0x%08x for stage %u",
                    &row[i]->fixed_fixed_size, i);
            row[i]->fixed_fixed_size = 0;
            row[i]->plastic_plastic_size = 0;
            row[i]->fixed_plastic_size = 0;
            write_address[i] = row[i]->fixed_fixed_data;
        } else {
            write_address[i] = NULL;
        }
        log_debug("write[%u] = 0x%08x", i, write_address[i]);
    }

    uint32_t max_delay_power_2 = max_delay_per_stage;
    uint32_t log_max_delay = 1;
    if (max_delay_power_2 != 1) {
        if (!is_power_of_2(max_delay_power_2)) {
            max_delay_power_2 = next_power_of_2(max_delay_power_2);
        }
        log_max_delay = ilog_2(max_delay_power_2);
    }


    // Go through the synapses
    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {
        // Post-neuron index
        uint32_t post_index = indices[synapse];

        // Weight
        uint16_t weight = weights[synapse];

        // Work out the delay stage and final value
        struct delay_value delay = get_delay(
            delays[synapse], max_stage, max_delay_per_stage);
        if (write_address[delay.stage] == NULL) {
            log_error("Delay stage %u has not been initialised; raw delay = %u,"
                    " delay = %u, max stage = %u", delay.stage, delays[synapse],
                    delay.delay, max_stage);
            rt_error(RTE_SWERR);
        }

        // Avoid errors when rows are full
        if (space[delay.stage] == 0) {
            log_warning("Row for delay stage %u is full - word not added!",
                    delay.stage);
            continue;
        }

        // Build synaptic word
        uint32_t word = build_static_word(
                weight, delay.delay, synapse_type, post_index, synapse_type_bits,
                synapse_index_bits, log_max_delay);

        // Write the word
        log_debug("Writing word to 0x%08x", &write_address[delay.stage][0]);
        write_address[delay.stage][0] = word;
        write_address[delay.stage] = &write_address[delay.stage][1];

        // Increment the size of the current row
        row[delay.stage]->fixed_fixed_size++;
        space[delay.stage]--;
    }
}
