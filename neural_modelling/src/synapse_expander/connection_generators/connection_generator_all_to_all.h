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
 * \dir
 * \brief Connection generators
 * \file
 * \brief All-to-All connection generator implementation
 */

#include <stdbool.h>
#include <synapse_expander/generator_types.h>

//! \brief The parameters to be passed around for this connector
//!
//! Specifies the range of pre- and post-neurons being connected.
struct all_to_all {
    uint32_t pre_lo;  //!< First index (inclusive) of range of pre-neurons
    uint32_t pre_hi;  //!< Last index (inclusive) of range of pre-neurons
    uint32_t post_lo; //!< First index (inclusive) of range of post-neurons
    uint32_t post_hi; //!< Last index (inclusive) of range of pre-neurons
    uint32_t allow_self_connections;
};

/**
 * \brief Initialise the all-to-all connection generator
 * \param[in,out] region: Region to read parameters from.  Should be updated
 *                        to position just after parameters after calling.
 * \return A data item to be passed in to other functions later on
 */
static void *connection_generator_all_to_all_initialise(address_t *region) {
    // Allocate the data structure for parameters
    struct all_to_all *params = spin1_malloc(sizeof(struct all_to_all));
    struct all_to_all *params_sdram = (void *) *region;

    // Copy the parameters into the data structure
    *params = *params_sdram++;
    *region = (void *) params_sdram;

    log_debug("All to all connector, pre_lo = %u, pre_hi = %u, "
            "post_lo = %u, post_hi = %u, allow_self_connections = %u",
            params->pre_lo, params->pre_hi, params->post_lo, params->post_hi,
            params->allow_self_connections);

    return params;
}

/**
 * \brief Free the all-to-all connection generator
 * \param[in] generator: The generator to free
 */
static void connection_generator_all_to_all_free(void *generator) {
    sark_free(generator);
}

/**
 * \brief Generate connections with the all-to-all connection generator
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
static uint32_t connection_generator_all_to_all_generate(
        void *generator, UNUSED uint32_t pre_slice_start,
        UNUSED uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    log_debug("Generating for %u", pre_neuron_index);

    struct all_to_all *obj = generator;

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // If not in the pre-population view range, then don't generate
    if ((pre_neuron_index < obj->pre_lo) ||
            (pre_neuron_index > obj->pre_hi)) {
        return 0;
    }

    // Add a connection to this pre-neuron for each post-neuron...
    uint32_t n_conns = 0;
    for (uint32_t i = 0; i < post_slice_count; i++) {
        // ... unless this is a self connection and these are disallowed
        if (!obj->allow_self_connections &&
                (pre_neuron_index == post_slice_start + i)) {
            log_debug("Not generating for post %u", post_slice_start + i);
            continue;
        }
        // ... or if the value is not in the range of the post-population view
        if ((i + post_slice_start < obj->post_lo) || (i + post_slice_start > obj->post_hi)) {
            continue;
        }
        indices[n_conns++] = i;
    }

    return n_conns;
}
