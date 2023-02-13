/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*!
 * \file
 * \brief implementation for handling the processing of synapse rows.
 *
 * \section row Synapse Row Representation
 * ```
 * |       Weight      |       Delay      |  Synapse Type   |   Neuron Index   |
 * |-------------------|------------------|-----------------|------------------|
 * |SYNAPSE_WEIGHT_BITS|SYNAPSE_DELAY_BITS|SYNAPSE_TYPE_BITS|SYNAPSE_INDEX_BITS|
 * |                   |                  |       SYNAPSE_TYPE_INDEX_BITS      |
 * ```
 * The API interface supports:
 *
 * - synapse_row_plastic_size()
 * - synapse_row_plastic_region()
 * - synapse_row_fixed_region()
 * - synapse_row_num_fixed_synapses()
 * - synapse_row_num_plastic_controls()
 * - synapse_row_plastic_controls()
 * - synapse_row_fixed_weight_controls()
 * - synapse_row_sparse_index()
 * - synapse_row_sparse_type()
 * - synapse_row_sparse_type_index()
 * - synapse_row_sparse_delay()
 * - synapse_row_sparse_weight()
 *
 * \section matrix Data Structure
 *
 * The data structure layout supported by this API is designed for
 * mixed plastic and fixed synapse rows.
 *
 * The data structure is treated as an array of 32-bit words.
 * Special meanings are ascribed to the 0th and 1st elements
 * of the array.
 *
 * We are expecting the original source address in SDRAM to be
 * in <code>row[0]</code>. The number of array elements in the plastic
 * region is held in the upper part of <code>row[1]</code>. A tag to indicate
 * the nature of the synaptic row structure is held in the lower
 * part of <code>row[1]</code>.
 * ```
 *   0:  [ N = <plastic elements>         | <tag> ]
 *   1:  [ First word of plastic region           ]
 *   ...
 *   N:  [ Last word of plastic region            ]
 * N+1:  [ First word of fixed region             ]
 *   ...
 *  M:   [ Last word of fixed region              ]
 * ```
 *
 * \section fixed Fixed and Fixed-Plastic Regions
 *
 * Within the fixed-region extracted using the above API, <code>fixed[0]</code>
 * contains the number of 32-bit fixed synaptic words, <code>fixed[1]</code>
 * contains the number of 16-bit plastic synapse control words.
 * (The weights for the plastic synapses are assumed to be stored
 * in some learning-rule-specific format in the plastic region)
 * ```
 *   0:           [ F = Num fixed synapses                                    ]
 *   1:           [ P = Size of plastic region in HALF-WORDS                  ]
 *   2:           [ First fixed synaptic word                                 ]
 *   ...
 * F+1:           [ Last fixed synaptic word                                  ]
 * F+2:           [ 1st plastic synapse control word|2nd plastic control word ]
 *   ...
 * F+1+ceil(P/2): [ Last word of fixed region                                 ]
 * ```
 * Note that \p P is effectively rounded up to a multiple of two for storage
 * purposes.
 */

#ifndef _SYNAPSE_ROW_H_
#define _SYNAPSE_ROW_H_

#include <common/neuron-typedefs.h>

//! how many bits the synapse weight will take
#ifndef SYNAPSE_WEIGHT_BITS
#define SYNAPSE_WEIGHT_BITS 16
#endif

#ifdef SYNAPSE_WEIGHTS_SIGNED
//! Define the type of the weights
typedef __int_t(SYNAPSE_WEIGHT_BITS) weight_t;
#else
//! Define the type of the weights
typedef __uint_t(SYNAPSE_WEIGHT_BITS) weight_t;
#endif
//! Define the type of the control data
typedef uint16_t control_t;

//! Number of header words per synaptic row
#define N_SYNAPSE_ROW_HEADER_WORDS 3

//! The type of the plastic-plastic part of the row
typedef struct {
    size_t size;                //!< The number of plastic words in `data`
    uint32_t data[];            //!< The plastic words, followed by the fixed part
} synapse_row_plastic_part_t;

//! The type of the fixed part of the row. The fixed-plastic part follows.
typedef struct {
    size_t num_fixed;           //!< The number of fixed synapses in `data`
    size_t num_plastic;         //!< The number of plastic controls in `data`
    uint32_t data[];            //!< The data, first the fixed then the plastic
} synapse_row_fixed_part_t;

typedef struct synapse_row_plastic_data_t synapse_row_plastic_data_t;

//! \brief Get the size of the plastic region
//! \param[in] row: The synaptic row
//! \return The size of the plastic region of the row
static inline size_t synapse_row_plastic_size(const synaptic_row_t row) {
    const synapse_row_plastic_part_t *the_row =
            (const synapse_row_plastic_part_t *) row;
    return the_row->size;
}

//! \brief Get the address of the plastic region
//! \param[in] row: The synaptic row
//! \return Pointer to the plastic region of the row
static inline synapse_row_plastic_data_t *synapse_row_plastic_region(
        synaptic_row_t row) {
    synapse_row_plastic_part_t *the_row = (synapse_row_plastic_part_t *) row;
    return (synapse_row_plastic_data_t *) the_row->data;
}

//! \brief Get the address of the non-plastic (or fixed) region
//! \param[in] row: The synaptic row
//! \return Address of the fixed region of the row
static inline synapse_row_fixed_part_t *synapse_row_fixed_region(
        synaptic_row_t row) {
    synapse_row_plastic_part_t *the_row = (synapse_row_plastic_part_t *) row;
    return (synapse_row_fixed_part_t *) &the_row->data[the_row->size];
}

//! \brief Get the number of fixed synapses in the row
//! \param[in] fixed: The fixed region of the synaptic row
//! \return Size of the fixed region of the row (in words)
static inline size_t synapse_row_num_fixed_synapses(
        const synapse_row_fixed_part_t *fixed) {
    return fixed->num_fixed;
}

//! \brief Get the number of plastic controls in the row
//! \param[in] fixed: The fixed region of the synaptic row
//! \return Size of the fixed-plastic region of the row (in _half_ words)
static inline size_t synapse_row_num_plastic_controls(
        const synapse_row_fixed_part_t *fixed) {
    return fixed->num_plastic;
}

//! \brief Get the array of plastic controls in the row
//! \param[in] fixed: The fixed region of the synaptic row
//! \return Address of the fixed-plastic region of the row
static inline control_t *synapse_row_plastic_controls(
        synapse_row_fixed_part_t *fixed) {
    return (control_t *) &fixed->data[fixed->num_fixed];
}

//! \brief The array of fixed weights in the row
//! \param[in] fixed: The fixed region of the synaptic row
//! \return Address of the fixed-fixed region of the row
static inline uint32_t *synapse_row_fixed_weight_controls(
        synapse_row_fixed_part_t *fixed) {
    return fixed->data;
}

// The following are offset calculations into the ring buffers
//! \brief Get the index
//! \param[in] x: The value to decode
//! \param[in] synapse_index_mask: Mask for the synapse index (depends on type)
//! \return the index
static inline index_t synapse_row_sparse_index(
        uint32_t x, uint32_t synapse_index_mask) {
    return x & synapse_index_mask;
}

//! \brief Get the type code
//! \param[in] x: The value to decode
//! \param[in] synapse_index_bits:
//!     Number of bits for the synapse index (depends on type)
//! \param[in] synapse_type_mask: Mask for the synapse type (depends on type)
//! \return the type code
static inline index_t synapse_row_sparse_type(
        uint32_t x, uint32_t synapse_index_bits, uint32_t synapse_type_mask) {
    return (x >> synapse_index_bits) & synapse_type_mask;
}

//! \brief Get the type and index
//! \param[in] x: The value to decode
//! \param[in] synapse_type_index_mask:
//!     Mask for the synapse type and index (depends on type)
//! \return the type and index (packed in the low bits of a word)
static inline index_t synapse_row_sparse_type_index(
        uint32_t x, uint32_t synapse_type_index_mask) {
    return x & synapse_type_index_mask;
}

//! \brief Get the delay from an encoded synapse descriptor
//! \param[in] x: The value to decode
//! \param[in] synapse_type_index_bits:
//!     Number of bits for the synapse type and index (depends on type)
//! \param[in] synapse_delay_mask: The mask for selecting the bits of the delay
//! \return the delay
static inline index_t synapse_row_sparse_delay(
        uint32_t x, uint32_t synapse_type_index_bits, uint32_t synapse_delay_mask) {
    return (x >> synapse_type_index_bits) & synapse_delay_mask;
}

//! \brief Get the weight from an encoded synapse descriptor
//! \param[in] x: The value to decode
//! \return the weight
static inline weight_t synapse_row_sparse_weight(uint32_t x) {
    return x >> (32 - SYNAPSE_WEIGHT_BITS);
}

//! \brief Converts a weight stored in a synapse row to an input
//! \param[in] weight: the weight to convert in synapse-row form
//! \param[in] left_shift: the shift to use when decoding
//! \return the actual input weight for the model
static inline input_t synapse_row_convert_weight_to_input(
        weight_t weight, uint32_t left_shift) {
    union {
        int_k_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (int_k_t) (weight) << left_shift;

    return converter.output_type;
}

//! \brief Get the index of the ring buffer for a given timestep, synapse type
//!     and neuron index
//! \param[in] simulation_timestep: The timestep
//! \param[in] synapse_type_index: The synapse type index
//! \param[in] neuron_index: The neuron index
//! \param[in] synapse_type_index_bits: Number of bits for type and index
//! \param[in] synapse_index_bits: Number of bits for index
//! \param[in] synapse_delay_mask: Mask for delay
//! \return Index into the ring buffer
static inline index_t synapse_row_get_ring_buffer_index(
        uint32_t simulation_timestep, uint32_t synapse_type_index,
        uint32_t neuron_index, uint32_t synapse_type_index_bits,
        uint32_t synapse_index_bits, uint32_t synapse_delay_mask) {
    return ((simulation_timestep & synapse_delay_mask) << synapse_type_index_bits)
            | (synapse_type_index << synapse_index_bits)
            | neuron_index;
}

//! \brief Get the index of the ring buffer for time 0, synapse type
//!     and neuron index
//! \param[in] synapse_type_index: The synapse type index
//! \param[in] neuron_index: The neuron index
//! \param[in] synapse_index_bits: Number of bits for index
//! \return Index into the ring buffer
static inline index_t synapse_row_get_ring_buffer_index_time_0(
        uint32_t synapse_type_index, uint32_t neuron_index,
        uint32_t synapse_index_bits) {
    return (synapse_type_index << synapse_index_bits) | neuron_index;
}

//! \brief Get the index of the first ring buffer for a given timestep
//! \param[in] simulation_timestep: The timestep
//! \param[in] synapse_type_index_bits: Number of bits for type and index
//! \param[in] synapse_delay_mask: Mask for delay
//! \return Index into the ring buffer
static inline index_t synapse_row_get_first_ring_buffer_index(
        uint32_t simulation_timestep, uint32_t synapse_type_index_bits,
        int32_t synapse_delay_mask) {
    return (simulation_timestep & synapse_delay_mask) << synapse_type_index_bits;
}

//! \brief Get the index of the ring buffer for a given timestep and combined
//!     synapse type and neuron index (as stored in a synapse row)
//! \param[in] simulation_timestep: The timestep
//! \param[in] combined_synapse_neuron_index:
//! \param[in] synapse_type_index_bits: Number of bits for type and index
//! \param[in] synapse_delay_mask: Mask for delay
//! \return Index into the ring buffer
static inline index_t synapse_row_get_ring_buffer_index_combined(
        uint32_t simulation_timestep,
        uint32_t combined_synapse_neuron_index,
        uint32_t synapse_type_index_bits, uint32_t synapse_delay_mask) {
    return ((simulation_timestep & synapse_delay_mask) << synapse_type_index_bits)
            | combined_synapse_neuron_index;
}

#endif  // SYNAPSE_ROW_H
