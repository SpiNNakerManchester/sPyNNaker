/*
 * Copyright (c) 2019 The University of Manchester
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

//! \file
//! \brief General types associated with generators
//!
//! Note that generators are really classes... except this is C so we have to
//! cheat.
#ifndef INCLUDED_GENERATOR_TYPES_H
#define INCLUDED_GENERATOR_TYPES_H

#include <common-typedefs.h>
#include <spin1_api.h>

#ifndef UNUSED
#define UNUSED __attribute__((__unused__))
#endif

/**
 * \brief The type of values used to indicate the subtype of generator to
 * create. Must match the constants on the Python side of the code.
 */
typedef uint32_t generator_hash_t;

/**
 * \brief How to initialise the generator; all generator types use the same
 * signature of initialiser
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
typedef void* (initialize_func)(address_t *region);

/**
 * \brief How to free any data for the generator; all generator types use
 * the same signature of free func
 * \param[in] data: The data to free
 */
typedef void (free_func)(void *data);

/**
 * \brief How to generate connections with a connection generator
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
typedef uint32_t (generate_connection_func)(
        void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices);

/**
 * \brief How to generate values with a parameter generator
 * \param[in] generator: The generator to use to generate values
 * \param[in] n_indices: The number of values to generate
 * \param[in] pre_neuron_index: The index of the neuron in the pre-population
 *                              being generated
 * \param[in] indices: The \p n_indices post-neuron indices for each connection
 * \param[out] values: An array into which to place the values; will be
 *                     \p n_indices in size
 */
typedef void (generate_param_func)(
        void *generator, uint32_t n_indices, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values);

/**
 * \brief How to generate a row of a matrix with a matrix generator
 * \param[in] generator: The data for the matrix generator, returned by the
 *                       initialise function
 * \param[out] synaptic_matrix: The address of the synaptic matrix to write to
 * \param[out] delayed_synaptic_matrix: The address of the synaptic matrix to
 *                                      write delayed connections to
 * \param[in] n_pre_neurons: The number of pre neurons to generate for
 * \param[in] pre_neuron_index: The index of the first pre neuron
 * \param[in] max_row_n_words: The maximum number of words in a normal row
 * \param[in] max_delayed_row_n_words: The maximum number of words in a
 *                                     delayed row
 * \param[in] synapse_type_bits: The number of bits used for the synapse type
 * \param[in] synapse_index_bits: The number of bits used for the neuron id
 * \param[in] synapse_type: The synapse type of each connection
 * \param[in] n_synapses: The number of synapses
 * \param[in] indices: Pointer to table of indices
 * \param[in] delays: Pointer to table of delays
 * \param[in] weights: Pointer to table of weights
 * \param[in] max_stage: The maximum delay stage to support
 * \param[in] max_delay_in_a_stage: max delay in a delay stage
 */
typedef void (generate_row_func)(
        void *generator,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage, uint32_t max_delay_in_a_stage);

#endif //INCLUDED_GENERATOR_TYPES_H
