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
 * \brief   Data type definitions for SpiNNaker Neuron-modelling
 * \details Defines a spike with either a payload or not and implements the
 *      functionality to extract the key and payload in both cases. If the
 *      spike is compiled as not having a payload, the payload will always be
 *      returned as 0.
 */

#ifndef __NEURON_TYPEDEFS_H__
#define __NEURON_TYPEDEFS_H__

#include <common-typedefs.h>
#include "maths-util.h"

#ifndef UNUSED
#define UNUSED __attribute__((__unused__))
#endif

//! The type of a SpiNNaker multicast message key word.
typedef uint32_t key_t;

//! The type of a SpiNNaker multicast message payload word.
typedef uint32_t payload_t;

#ifdef SPIKES_WITH_PAYLOADS
//! The type of a spike
typedef uint64_t spike_t;

union _spike_t {
    spike_t pair;
    struct {
        payload_t payload;
        key_t key;
    };
};
#else  /*SPIKES_WITHOUT_PAYLOADS*/
//! The type of a spike
typedef uint32_t spike_t;
#endif /*SPIKES_WITH_PAYLOADS*/

//! \brief Retrieve the key from a spike.
//! \param[in] s: the spike to get the key from
//! \return the key from the spike
static inline key_t spike_key(spike_t s) {
#ifdef SPIKES_WITH_PAYLOADS
    union _spike_t spike;
    spike.pair = s;
    return spike.key;
#else  /*SPIKES_WITHOUT_PAYLOADS*/
    return s;
#endif /*SPIKES_WITH_PAYLOADS*/
}

//! \brief Retrieve the payload from a spike.
//! \param[in] s: the spike to get the payload from
//! \return the payload from the spike; always zero when `SPIKES_WITH_PAYLOADS`
//!     is not defined.
static inline payload_t spike_payload(spike_t s) {
#ifdef SPIKES_WITH_PAYLOADS
    union _spike_t spike;
    spike.pair = s;
    return spike.payload;
#else  /*SPIKES_WITHOUT_PAYLOADS*/
    use(s);
    return 0;
#endif /*SPIKES_WITH_PAYLOADS*/
}

//! The type of a synaptic row.
typedef address_t synaptic_row_t;

//! The type of an input.
typedef REAL input_t;

//! The type of a state variable.
typedef REAL state_t;

#endif /* __NEURON_TYPEDEFS_H__ */
