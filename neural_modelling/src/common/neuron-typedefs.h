/*
 * neuron-typedefs.h
 *
 *
 *  SUMMARY
 *    Data type definitions for SpiNNaker Neuron-modelling
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *
 *
 *  CREATION DATE
 *    10 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 10 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#ifndef __NEURON_TYPEDEFS_H__
#define __NEURON_TYPEDEFS_H__

#include <common-typedefs.h>

#ifndef __SPIKE_T__

typedef uint32_t key_t;
typedef uint32_t payload_t;

#ifdef SPIKES_WITH_PAYLOADS

typedef uint64_t spike_t;

static inline key_t spike_key(spike_t s) {
    return ((key_t)(s >> 32));
}

static inline payload_t spike_payload (spike_t s) {
    return ((payload_t)(s & UINT32_MAX));
}

#else  /*SPIKES_WITH_PAYLOADS*/

typedef uint32_t spike_t;

static inline key_t spike_key(spike_t s) {
    return (s);
}
static inline payload_t spike_payload(spike_t s) {
    use(s);
    return (0);
}

#endif /*SPIKES_WITH_PAYLOADS*/

#endif /*__SPIKE_T__*/

// types
typedef uint16_t row_size_t;
typedef address_t synaptic_row_t;

// The type of units.
typedef accum current_t;
typedef unsigned long fract decay_t;
typedef accum scale_factor_t;
typedef accum voltage_t;
typedef accum resistance_t;
#define current_0 (kbits (0))

// Enumeration defining the bits of the system word
typedef enum system_data_e {
    e_system_data_record_spike_history = (1 << 0),
    e_system_data_record_neuron_potential = (1 << 1),
    e_system_data_record_neuron_gsyn = (1 << 2),
} system_data_e;

typedef unsigned long fract synapse_input_t;

#ifndef SYNAPSE_INDEX_BITS
#define SYNAPSE_INDEX_BITS 8
#endif

#ifndef SYNAPSE_DELAY_BITS
#define SYNAPSE_DELAY_BITS 4
#endif

#ifndef SYNAPSE_WEIGHT_BITS
#define SYNAPSE_WEIGHT_BITS 16
#endif

#ifndef RING_ENTRY_BITS
#define RING_ENTRY_BITS SYNAPSE_WEIGHT_BITS
#endif

#ifndef CURRENT_BITS
#define CURRENT_BITS (sizeof(current_t)*8)
#endif

#ifndef DECAY_BITS
#define DECAY_BITS CURRENT_BITS
#endif

#ifdef  SYNAPSE_WEIGHTS_SIGNED
typedef __int_t(RING_ENTRY_BITS) ring_entry_t;
typedef __int_t(SYNAPSE_WEIGHT_BITS) weight_t;
#else
typedef __uint_t(SYNAPSE_WEIGHT_BITS)   weight_t;
typedef __uint_t(RING_ENTRY_BITS)     ring_entry_t;
#endif

//             |       Weights       |       Delay        |       Type        |      Index         |
//             |---------------------|--------------------|-------------------|--------------------|
// Bit count   | SYNAPSE_WEIGHT_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
//             |                     |                    |        SYNAPSE_TYPE_INDEX_BITS         |
//             |---------------------|--------------------|----------------------------------------|
#define SYNAPSE_TYPE_INDEX_BITS (SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS)

#define SYNAPSE_DELAY_MASK      ((1 << SYNAPSE_DELAY_BITS) - 1)
#define SYNAPSE_TYPE_MASK       ((1 << SYNAPSE_TYPE_BITS) - 1)
#define SYNAPSE_INDEX_MASK      ((1 << SYNAPSE_INDEX_BITS) - 1)
#define SYNAPSE_TYPE_INDEX_MASK ((1 << SYNAPSE_TYPE_INDEX_BITS) - 1)

// Where key is stored in spike ids
#define KEY_SHIFT 11
#define KEY_MASK  ((1 << KEY_SHIFT) - 1)

// Default buffer/array sizes
//
// The first three are calculated from the number of bits in
// the various representations
// (and should be altered by changing the number of bits used).
//
// The remainder can be given different sizes at compile-time,
// by using -D<name>=<new_value>
#define MAX_NEURON_SIZE     (1 << SYNAPSE_INDEX_BITS)
#define MASTER_POPULATION_MAX  1152
#define ROW_SIZE_TABLE_MAX  8
#define CURRENT_BUFFER_SIZE (1 << (SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS))
#define RING_BUFFER_SIZE    (1 << (SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_BITS\
                             + SYNAPSE_INDEX_BITS))

// The amount of space in the incoming spike buffer
#ifndef IN_SPIKE_SIZE
#define IN_SPIKE_SIZE 256
#endif

// DMA Buffer is 256 words for entries + 3 header words
#ifndef DMA_BUFFER_SIZE
#define DMA_BUFFER_SIZE            259
#endif

#endif /* __NEURON_TYPEDEFS_H__ */
