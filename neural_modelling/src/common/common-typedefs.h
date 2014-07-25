/*
 * spin-neuron-typedefs.h
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

#ifndef __SPIN_NEURON_TYPEDEFS_H__
#define __SPIN_NEURON_TYPEDEFS_H__

#include <stdint.h>
#include <stdbool.h>
#include <stdfix.h>
#include "stdfix-full-iso.h"

// Pseudo-function Declarations

// The following can be used to silence gcc's "-Wall -Wextra"
// warnings about failure to use function arguments.
//
// Obviously you'll only be using this during debug, for unused
// arguments of callback functions, or where conditional compilation
// means that the accessor functions return a constant

#ifndef use
#define use(x) do {} while ((x)!=(x))
#endif

// Define int/uint helper macros to create the correct
// type names for int/uint of a particular size.
//
// This requires an extra level of macro call to "stringify"
// the result.

#define __int_helper(b) int ## b ## _t
#define __uint_helper(b) uint ## b ## _t
#define __int_t(b) __int_helper(b)
#define __uint_t(b) __uint_helper(b)

// Give meaningful names to the common types.
// (checking that they haven't already been declared.)

#ifndef __SIZE_T__
typedef uint32_t size_t;
#define __SIZE_T__
#endif /*__SIZE_T__*/

#ifndef __INDEX_T__
typedef uint32_t index_t;
#define __INDEX_T__
#endif /*__INDEX_T__*/

#ifndef __COUNTER_T__
typedef uint32_t counter_t;
#define __COUNTER_T__
#endif /*__COUNTER_T__*/

#ifndef __TIMER_T__
typedef uint32_t timer_t;
#define __TIMER_T__
#endif /*__TIMER_T__*/

#ifndef __ADDRESS_T__
typedef uint32_t* address_t;
#define __ADDRESS_T__
#endif /*__ADDRESS_T__*/

#ifndef __SPIKE_T__
typedef uint32_t  key_t;
typedef uint32_t  payload_t;
#ifdef SPIKES_WITH_PAYLOADS
typedef uint64_t  spike_t;
static inline key_t     spike_key     (spike_t s)
{ return ((key_t)(s >> 32)); }
static inline payload_t spike_payload (spike_t s)
{ return ((payload_t)(s & UINT32_MAX)); }
#else  /*SPIKES_WITH_PAYLOADS*/
typedef uint32_t  spike_t;
static inline key_t     spike_key     (spike_t s) {         return (s); }
static inline payload_t spike_payload (spike_t s) { use(s); return (0); }
#endif /*SPIKES_WITH_PAYLOADS*/
#endif /*__SPIKE_T__*/

// types
typedef uint16_t  row_size_t;
typedef address_t synaptic_row_t;

// The type of units.
typedef accum                    current_t;
typedef unsigned long fract      decay_t;
typedef accum                    scale_factor_t;
typedef accum                    voltage_t;
typedef accum                    resistance_t;
#define current_0 (kbits (0))

// Enumeration defining the bits of the system word
typedef enum system_data_e
{
  e_system_data_record_spike_history    = (1 << 0),
  e_system_data_record_neuron_potential = (1 << 1),
  e_system_data_record_neuron_gsyn      = (1 << 2),
} system_data_e;

typedef enum recording_channel_e
{
  e_recording_channel_spike_history,
  e_recording_channel_neuron_potential,
  e_recording_channel_neuron_gsyn,
  e_recording_channel_max,
} recording_channel_e;


typedef unsigned long fract      synapse_input_t;

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
typedef  __int_t(RING_ENTRY_BITS)    ring_entry_t;
typedef  __int_t(SYNAPSE_WEIGHT_BITS) weight_t;
#else
typedef __uint_t(SYNAPSE_WEIGHT_BITS) weight_t;
typedef  __uint_t(RING_ENTRY_BITS)   ring_entry_t;
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
#define RING_BUFFER_SIZE    (1 << (SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS))

#ifndef IN_SPIKE_SIZE
#define IN_SPIKE_SIZE 256
#endif

#ifndef SYNAPTIC_ROW_DATA_MAX
#define SYNAPTIC_ROW_DATA_MAX      (18*64) /* = 1152 */
#endif

#ifndef DMA_BUFFER_SIZE
#define DMA_BUFFER_SIZE            259
#endif

#ifndef OUT_SPIKE_SIZE
#define OUT_SPIKE_SIZE             (MAX_NEURON_SIZE >> 5)
#endif

#endif /* __SPIN_NEURON_TYPEDEFS_H__ */
