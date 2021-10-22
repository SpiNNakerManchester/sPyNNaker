/*!
 * \file
 * \brief implementation for handling the processing of synapse rows.
 * \details
 * Synapse Row Representation:
 * |       Weight      |       Delay      |  Synapse Type   |   Neuron Index   |
 * |-------------------|------------------|-----------------|------------------|
 * |SYNAPSE_WEIGHT_BITS|SYNAPSE_DELAY_BITS|SYNAPSE_TYPE_BITS|SYNAPSE_INDEX_BITS|
 * |                   |                  |       SYNAPSE_TYPE_INDEX_BITS      |
 * The API interface supports:
 * - synapse_row_plastic_size(row)
 * - synapse_row_plastic_region(row)
 * - synapse_row_fixed_region(row)
 * - synapse_row_num_fixed_synapses(fixed)
 * - synapse_row_num_plastic_controls(fixed)
 * - synapse_row_plastic_controls(fixed)
 * - synapse_row_fixed_weight_controls(fixed)
 * - synapse_row_sparse_index(x)
 * - synapse_row_sparse_type(x)
 * - synapse_row_sparse_type_index(x)
 * - synapse_row_sparse_delay(x)
 * - synapse_row_sparse_weight(x)
 *  */

#ifndef _SYNAPSE_ROW_H_
#define _SYNAPSE_ROW_H_

#include <common/neuron-typedefs.h>

//! how many bits the synapse weight will take
#ifndef SYNAPSE_WEIGHT_BITS
#define SYNAPSE_WEIGHT_BITS 16
#endif

//! how many bits the synapse delay will take
#ifndef SYNAPSE_DELAY_BITS
#define SYNAPSE_DELAY_BITS 4
#endif

// Create some masks based on the number of bits
//! the mask for the synapse delay in the row
#define SYNAPSE_DELAY_MASK      ((1 << SYNAPSE_DELAY_BITS) - 1)

#define SYNAPSE_WEIGHTS_SIGNED true


// Define the type of the weights
#ifdef SYNAPSE_WEIGHTS_SIGNED
typedef __int_t(SYNAPSE_WEIGHT_BITS) weight_t;
io_printf(IO_BUF, "Using signed weights!! \n ");
#else
typedef __uint_t(SYNAPSE_WEIGHT_BITS) weight_t;
#endif
typedef uint16_t control_t;

#define N_SYNAPSE_ROW_HEADER_WORDS 3


// The data structure layout supported by this API is designed for
// mixed plastic and fixed synapse rows.
//
// The data structure is treated as an array of 32-bit words.
// Special meanings are ascribed to the 0th and 1st elements
// of the array.
//
// We are expecting the original source address in SDRAM to be
// in location 0. The number of array elements in the plastic
// region is held in the upper part of row[1]. A tag to indicate
// the nature of the synaptic row structure is held in the lower
// part of row[1].
//
//   0:  [ N = <plastic elements>         | <tag> ]
//   1:  [ First word of plastic region           ]
//   ...
//   N:  [ Last word of plastic region            ]
// N+1:  [ First word of fixed region             ]
//   ...
//  M:   [ Last word of fixed region              ]

static inline size_t synapse_row_plastic_size(address_t row) {
    return (size_t) row[0];
}

// Returns the address of the plastic region
static inline address_t synapse_row_plastic_region(address_t row) {
    return ((address_t) (&(row[1])));
}

// Returns the address of the non-plastic (or fixed) region
static inline address_t synapse_row_fixed_region(address_t row) {
    return ((address_t) (&(row[synapse_row_plastic_size(row) + 1])));
}

// Within the fixed-region extracted using the above API, fixed[0]
// Contains the number of 32-bit fixed synaptic words, fixed[1]
// Contains the number of 16-bit plastic synapse control words
// (The weights for the plastic synapses are assumed to be stored
// In some learning-rule-specific format in the plastic region)
//   0:           [ F = Num fixed synapses                                    ]
//   1:           [ P = Size of plastic region in WORDS                       ]
//   2:           [ First fixed synaptic word                                 ]
//   ...
// F+1:           [ Last fixed synaptic word                                  ]
// F+2:           [ 1st plastic synapse control word|2nd plastic control word ]
//   ...
// F+1+ceil(P/2): [ Last word of fixed region                                 ]
static inline size_t synapse_row_num_fixed_synapses(address_t fixed) {
    return ((size_t) (fixed[0]));
}

static inline size_t synapse_row_num_plastic_controls(address_t fixed) {
    return ((size_t) (fixed[1]));
}

static inline control_t* synapse_row_plastic_controls(address_t fixed) {
    return (control_t*) (&fixed[2 + synapse_row_num_fixed_synapses(fixed)]);
}

static inline uint32_t *synapse_row_fixed_weight_controls(address_t fixed) {
    return (&(fixed[2]));
}

// The following are offset calculations into the ring buffers
static inline index_t synapse_row_sparse_index(
        uint32_t x, uint32_t synapse_index_mask) {
    return (x & synapse_index_mask);
}

static inline index_t synapse_row_sparse_type(
        uint32_t x, uint32_t synapse_index_bits, uint32_t synapse_type_mask) {
    return ((x >> synapse_index_bits) & synapse_type_mask);
}

static inline index_t synapse_row_sparse_type_index(
        uint32_t x, uint32_t synapse_type_index_mask) {
    return (x & synapse_type_index_mask);
}

static inline index_t synapse_row_sparse_delay(
        uint32_t x, uint32_t synapse_type_index_bits) {
    return ((x >> synapse_type_index_bits) & SYNAPSE_DELAY_MASK);
}

static inline weight_t synapse_row_sparse_weight(uint32_t x) {
    return (x >> (32 - SYNAPSE_WEIGHT_BITS));
}

#endif  // SYNAPSE_ROW_H
