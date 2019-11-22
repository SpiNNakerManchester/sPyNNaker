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

/*! \file
 *
 *
 * neuron-typedefs.h
 *
 *
 *  SUMMARY
 * \brief   Data type definitions for SpiNNaker Neuron-modelling
 *
 */

#ifndef __NEURON_TYPEDEFS_H__
#define __NEURON_TYPEDEFS_H__

#include <common-typedefs.h>
#include "maths-util.h"

// Determine the type of a spike
/*
 * defines a spike with either a pay load or not and implements the
 * functionality to extract the key and pay load in both cases. If the
 * spike is compiled as not having a pay load, the pay load will always be
 * returned as 0
 */
#ifndef __SPIKE_T__

typedef uint32_t key_t;
typedef uint32_t payload_t;

#ifdef SPIKES_WITH_PAYLOADS

typedef uint64_t spike_t;

//! \brief helper method to retrieve the key from a spike
//! \param[in] s: the spike to get the key from
//! \return key_t: the key from the spike
static inline key_t spike_key(spike_t s) {
    return (key_t) (s >> 32);
}

//! \brief helper method to retrieve the pay-load from a spike
//! \param[in] s: the spike to get the pay-load from
//! \return payload_t: the pay-load from the spike (only used if the model
//! is compiled with SPIKES_WITH_PAYLOADS)
static inline payload_t spike_payload (spike_t s) {
    return (payload_t) (s & UINT32_MAX);
}

#else  /*SPIKES_WITHOUT_PAYLOADS*/

typedef uint32_t spike_t;

//! \brief helper method to retrieve the key from a spike
//! \param[in] s: the spike to get the key from
//! \return key_t: the key from the spike
static inline key_t spike_key(spike_t s) {
    return s;
}

//! \brief helper method to retrieve the pay-load from a spike
//! \param[in] s: the spike to get the pay-load from
//! \return payload_t: the pay-load from the spike (default-ly set to zero if
//!                    the model is not compiled with SPIKES_WITH_PAYLOADS)

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
