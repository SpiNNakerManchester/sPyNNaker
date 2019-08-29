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

#ifndef INCLUDED_GENERATOR_TYPES_H
#define INCLUDED_GENERATOR_TYPES_H

#include <common-typedefs.h>
#include <spin1_api.h>

/**
 *! \brief The type of values used to indicate the subtype of generator to
 *! create. Must match the constants on the Python side of the code.
 */
typedef uint32_t generator_hash_t;

/**
 *! \brief How to initialise the generator; all generator types use the same
 *! signature of initialiser
 *! \param[in/out] region Region to read parameters from.  Should be updated
 *!                       to position just after parameters after calling.
 *! \return A data item to be passed in to other functions later on
 */
typedef void* (initialize_func)(address_t *region);

/**
 *! \brief How to free any data for the generator; all generator types use
 *! the same signature of free func
 *! \param[in] data The data to free
 */
typedef void (free_func)(void *data);

/**
 *! \brief How to generate connections with a connection generator
 *! \param[in] generator The generator to use to generate connections
 *! \param[in] pre_slice_start The start of the slice of the pre-population
 *!                            being generated
 *! \param[in] pre_slice_count The number of neurons in the slice of the
 *!                            pre-population being generated
 *! \param[in] pre_neuron_index The index of the neuron in the pre-population
 *!                             being generated
 *! \param[in] post_slice_start The start of the slice of the post-population
 *!                             being generated
 *! \param[in] post_slice_count The number of neurons in the slice of the
 *!                             post-population being generated
 *! \param[in] max_row_length The maximum number of connections to generate
 *! \param[in/out] indices An array into which the core-relative post-indices
 *!                        should be placed.  This will be initialised to be
 *!                        max_row_length in size
 *! \return The number of connections generated
 */
typedef uint32_t (generate_connection_func)(
        void *generator, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices);

/**
 *! \brief How to generate values with a parameter generator
 *! \param[in] generator The generator to use to generate values
 *! \param[in] n_indices The number of values to generate
 *! \param[in] pre_neuron_index The index of the neuron in the pre-population
 *!                             being generated
 *! \param[in] indices The n_indices post-neuron indices for each connection
 *! \param[in/out] values An array into which to place the values - will be
 *!                       n_indices in size
 */
typedef void (generate_param_func)(
        void *generator, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values);

/**
 *! \brief How to generate a row of a matrix with a matrix generator
 *! \param[in] generator The data for the matrix generator, returned by the
 *!                      initialise function
 *! \param[in] synaptic_matrix The address of the synaptic matrix to write to
 *! \param[in] delayed_synaptic_matrix The address of the synaptic matrix to
 *!                                    write delayed connections to
 *! \param[in] max_row_n_words The maximum number of words in a normal row
 *! \param[in] max_delayed_row_n_words The maximum number of words in a
 *!                                     delayed row
 *! \param[in] max_row_n_synapses The maximum number of synapses in a
 *!                               normal row
 *! \param[in] max_delayed_row_n_synapses The maximum number of synapses in
 *!                                       a delayed row
 *! \param[in] n_synapse_type_bits The number of bits used for the synapse type
 *! \param[in] n_synapse_index_bits The number of bits used for the neuron id
 *! \param[in] synapse_type The synapse type of each connection
 *! \param[in] weight_scales An array of weight scales, one for each synapse
 *!                          type
 *! \param[in] post_slice_start The start of the slice of the
 *!                             post-population being generated
 *! \param[in] post_slice_count The number of neurons in the slice of the
 *!                             post-population being generated
 *! \param[in] pre_slice_start The start of the slice of the pre-population
 *!                            being generated
 *! \param[in] pre_slice_count The number of neurons in the slice of the
 *!                            pre-population being generated
 *! \param[in] connection_generator The generator of connections
 *! \param[in] delay_generator The generator of delay values
 *! \param[in] weight_generator The generator of weight values
 *! \param[in] max_stage The maximum delay stage to support
 *! \param[in] timestep_per_delay The delay value multiplier to get to timesteps
 */
typedef void (generate_row_func)(
        void *generator,
        address_t synaptic_matrix, address_t delayed_synaptic_matrix,
        uint32_t n_pre_neurons, uint32_t pre_neuron_index,
        uint32_t max_row_n_words, uint32_t max_delayed_row_n_words,
        uint32_t synapse_type_bits, uint32_t synapse_index_bits,
        uint32_t synapse_type, uint32_t n_synapses,
        uint16_t *indices, uint16_t *delays, uint16_t *weights,
        uint32_t max_stage);

#endif //INCLUDED_GENERATOR_TYPES_H
