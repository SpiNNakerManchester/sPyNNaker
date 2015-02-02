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
#include "maths-util.h"

// Determine the type of a spike
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

// The type of a synaptic row
typedef address_t synaptic_row_t;

// The type of an input
typedef REAL input_t;

// The type of a state variable
typedef REAL state_t;

#endif /* __NEURON_TYPEDEFS_H__ */
