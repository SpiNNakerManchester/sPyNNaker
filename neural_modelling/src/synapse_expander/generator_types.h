/*
 * Copyright (c) 2019 The University of Manchester
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

//! \file
//! \brief General types associated with generators
//!
//! Note that generators are really classes... except this is C so we have to
//! cheat.
#ifndef INCLUDED_GENERATOR_TYPES_H
#define INCLUDED_GENERATOR_TYPES_H

#include <common-typedefs.h>
#include <spin1_api.h>
#include "param_generator.h"
#include "matrix_generator.h"

#ifndef UNUSED
#define UNUSED __attribute__((__unused__))
#endif

/**
 * \brief The type of values used to indicate the subtype of generator to
 * create. Must match the constants on the Python side of the code.
 */
typedef uint32_t generator_hash_t;

/**
 * \brief How to initialise the param generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
typedef void* (initialize_param_func)(void **region);

/**
 * \brief How to initialise the connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
typedef void* (initialize_connector_func)(void **region);

/**
 * \brief How to initialise the matrix generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \param[in] synaptic_matrix: The address of the base of the synaptic matrix
 * \return A data item to be passed in to other functions later on
 */
typedef void* (initialize_matrix_func)(void **region, void *synaptic_matrix);

/**
 * \brief How to free any data for the generator; all generator types use
 * the same signature of free func
 * \param[in] data: The data to free
 */
typedef void (free_func)(void *data);

/**
 * \brief How to generate values with a parameter generator
 * \param[in] generator: The generator to use to generate values
 * \return The value generated
 */
typedef accum (generate_param_func)(void *generator);

/**
 * \brief How to write a synapse to a matrix
 * \param[in] generator: The generator data
 * \param[in] pre_index: The index of the pre-neuron relative to the start of
 *                       the matrix
 * \param[in] post_index: The index of the post-neuron on this core
 * \param[in] weight: The weight of the synapse in raw numbers
 * \param[in] delay: The delay of the synapse in time steps
 * \param[in] weight_scale: The scaling to apply to the weight if needed
 * \return: Whether the synapse was added or not
 */
typedef bool (write_synapse_func)(void *generator,
        uint32_t pre_index, uint16_t post_index, accum weight, uint16_t delay,
		unsigned long accum weight_scale);

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
 * \return Whether connections have been generated successfully
 */
typedef bool (generate_connection_func)(
        void *generator, uint32_t pre_lo, uint32_t pre_hi,
        uint32_t post_lo, uint32_t post_hi, uint32_t post_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        unsigned long accum weight_scale, accum timestep_per_delay,
        param_generator_t weight_generator, param_generator_t delay_generator,
        matrix_generator_t matrix_generator);

//! \brief Rescales a delay to account for timesteps and type-converts it
//! \param[in] delay: the delay to rescale
//! \param[in] timestep_per_delay: The timestep unit
//! \return the rescaled delay
static inline uint16_t rescale_delay(accum delay, accum timestep_per_delay) {
    accum ts_delay = delay * timestep_per_delay;
    if (ts_delay < 0) {
        ts_delay = 1;
    }
    uint16_t delay_int = (uint16_t) ts_delay;
    if (ts_delay != delay_int) {
        log_debug("Rounded delay %k to %u", delay, delay_int);
    }
    return delay_int;
}

//! \brief Rescales a weight to account for weight granularity and
//!     type-converts it
//! \param[in] weight: the weight to rescale
//! \param[in] weight_scale: The weight scaling factor
//! \return the rescaled weight
static inline uint16_t rescale_weight(accum weight, unsigned long accum weight_scale) {
    unsigned long accum uweight = 0;
	if (weight < 0) {
        uweight = -weight;
    } else {
    	uweight = weight;
    }
    unsigned long accum weight_scaled = uweight * weight_scale;
    unsigned long accum weight_rounded = roundulk(weight_scaled, 32);
    uint16_t weight_int = (uint16_t) (bitsulk(weight_rounded) >> 32);
    if (weight_scaled != weight_int) {
        log_debug("Rounded weight %k to %u (scale is %k)",
                weight_scaled, weight_int, weight_scale);
    }
    return weight_int;
}

#define max(a, b) (a > b? a: b)

#endif //INCLUDED_GENERATOR_TYPES_H
