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
 *! \file
 *! \brief Static synaptic matrix implementation
 */

#include <stdbool.h>
#include <debug.h>
#include <delay_extension/delay_extension.h>
#include "matrix_generator_common.h"
#include <synapse_expander/generator_types.h>

static initialize_func matrix_generator_static_initialize;
static free_func matrix_generator_static_free;
static generate_row_func matrix_generator_static_write_row;

static void *matrix_generator_static_initialize(address_t *region) {
    use(region);
    return NULL;
}

static void matrix_generator_static_free(void *data) {
    use(data);
}

/**
 *! \brief The shift of the weight within a synaptic word
 */
#define SYNAPSE_WEIGHT_SHIFT 16

/**
 *! \brief The mask of a weight before shifting
 */
#define SYNAPSE_WEIGHT_MASK 0xFFFF

/**
 *! \brief The mask of a delay before shifting
 */
#define SYNAPSE_DELAY_MASK 0xFF

/**
 *! \brief The position of the plastic-plastic size within a row
 */
#define STATIC_PLASTIC_PLASTIC_SIZE 0

/**
 *! \brief The position of the fixed-plastic size within a row
 */
#define STATIC_FIXED_PLASTIC_SIZE 2

/**
 *! \brief The position of the fixed-fixed size within a row
 */
#define STATIC_FIXED_FIXED_SIZE 1

/**
 *! \brief The starting position of the fixed-fixed data within a row
 */
#define STATIC_FIXED_FIXED_OFFSET 3

/**
 *! \brief Build a static synaptic word from components
 *! \param[in] weight The weight of the synapse
 *! \param[in] delay The delay of the synapse
 *! \param[in] type The synapse type
 *! \param[in] post_index The core-relative index of the target neuron
 *! \param[in] synapse_type_bits The number of bits for the synapse type
 *! \param[in] synapse_index_bits The number of bits for the target neuron id
 *! \return a synaptic word
 */
static uint32_t build_static_word(
        uint16_t weight, uint16_t delay, uint32_t type,
        uint16_t post_index, uint32_t synapse_type_bits,
        uint32_t synapse_index_bits) {
    uint32_t synapse_index_mask = (1 << synapse_index_bits) - 1;
    uint32_t synapse_type_mask = (1 << synapse_type_bits) - 1;

    uint32_t wrd  = post_index & synapse_index_mask;
    wrd |= (type & synapse_type_mask) << synapse_index_bits;
    wrd |= (delay & SYNAPSE_DELAY_MASK) <<
            (synapse_index_bits + synapse_type_bits);
    wrd |= (weight & SYNAPSE_WEIGHT_MASK) << SYNAPSE_WEIGHT_SHIFT;
    return wrd;
}

static void matrix_generator_static_write_row(
        void *data,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage) {
    use(data);

    log_debug("Max stage = %u", max_stage);

    // Row address and position for each possible delay stage (including no
    // delay stage)
    address_t row_address[max_stage];

    // The space available on each row
    uint16_t space[max_stage];

    // The normal row position and space available - might be 0 if all delayed
    row_address[0] = NULL;
    space[0] = max_row_n_words;
    if (synaptic_matrix != NULL) {
        row_address[0] =
                &synaptic_matrix[pre_neuron_index * (max_row_n_words + 3)];
    }
    log_debug("row[0] = 0x%08x", row_address[0]);

    // The delayed row positions and space available
    if (delayed_synaptic_matrix != NULL) {
        address_t delayed_address = &delayed_synaptic_matrix[
                pre_neuron_index * (max_delayed_row_n_words + 3)];
        uint32_t single_matrix_size =
                n_pre_neurons * (max_delayed_row_n_words + 3);
        for (uint32_t i = 1; i < max_stage; i++) {
            row_address[i] = &delayed_address[single_matrix_size * (i - 1)];
            space[i] = max_delayed_row_n_words;
            log_debug("row[%u] = 0x%08x", i, row_address[i]);
        }
    } else {
        for (uint32_t i = 1; i < max_stage; i++) {
            row_address[i] = NULL;
            space[i] = 0;
            log_debug("row[%u] = 0x%08x", i, row_address[i]);
        }
    }

    // The address to write synapses to on each stage
    address_t write_address[max_stage];
    for (uint32_t i = 0; i < max_stage; i++) {
        if (row_address[i] != NULL) {
            log_debug("Row size at 0x%08x for stage %u",
                    &row_address[i][STATIC_FIXED_FIXED_SIZE], i);
            row_address[i][STATIC_FIXED_FIXED_SIZE] = 0;
            row_address[i][STATIC_PLASTIC_PLASTIC_SIZE] = 0;
            row_address[i][STATIC_FIXED_PLASTIC_SIZE] = 0;
            write_address[i] = &row_address[i][STATIC_FIXED_FIXED_OFFSET];
        } else {
            write_address[i] = NULL;
        }
        log_debug("write[%u] = 0x%08x", i, write_address[i]);
    }


    // Go through the synapses
    for (uint32_t synapse = 0; synapse < n_synapses; synapse++) {
        // Post-neuron index
        uint32_t post_index = indices[synapse];

        // Weight
        uint16_t weight = weights[synapse];

        // Work out the delay stage and final value
        struct delay_value delay = get_delay(delays[synapse], max_stage);
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
                synapse_index_bits);

        //io_printf(IO_BUF, "weight: %d, delay %d, syn type %d\n", weight, delay.delay, synapse_type);

        // Write the word
        log_debug("Writing word to 0x%08x", &write_address[delay.stage][0]);
        write_address[delay.stage][0] = word;
        write_address[delay.stage] = &write_address[delay.stage][1];

        // Increment the size of the current row
        row_address[delay.stage][STATIC_FIXED_FIXED_SIZE]++;
        space[delay.stage]--;
    }
}
