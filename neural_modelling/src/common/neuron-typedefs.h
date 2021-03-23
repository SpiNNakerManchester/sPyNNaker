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

// Determine the type of a spike
#ifndef __SPIKE_T__

//! The type of a SpiNNaker multicast message key word
typedef uint32_t key_t;
//! The type of a SpiNNaker multicast message payload word
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

//! \brief helper method to retrieve the key from a spike
//! \param[in] s: the spike to get the key from
//! \return key_t: the key from the spike
static inline key_t spike_key(spike_t s) {
    union _spike_t spike;
    spike.pair = s;
    return spike.key;
}

//! \brief helper method to retrieve the pay-load from a spike
//! \param[in] s: the spike to get the pay-load from
//! \return payload_t: the pay-load from the spike (only used if the model
//!     is compiled with SPIKES_WITH_PAYLOADS)
static inline payload_t spike_payload(spike_t s) {
    union _spike_t spike;
    spike.pair = s;
    return spike.payload;
}

#else  /*SPIKES_WITHOUT_PAYLOADS*/

//! The type of a spike
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
static inline payload_t spike_payload(UNUSED spike_t s) {
    return 0;
}
#endif /*SPIKES_WITH_PAYLOADS*/
#endif /*__SPIKE_T__*/

//! \brief The type of a synaptic row.
//! \details There is no definition of `struct synaptic row` because it is a
//!     form of memory structure that C cannot encode as a single `struct`.
//!
//! It's actually this, with multiple variable length arrays intermixed with
//! size counts:
//! ~~~~~~{.c}
//! struct synaptic_row {
//!     uint32_t n_plastic_synapse_words;
//!     uint32_t plastic_synapse_data[n_plastic_synapse_words]; // VLA
//!     uint32_t n_fixed_synapse_words;
//!     uint32_t n_plastic_controls;
//!     uint32_t fixed_synapse_data[n_fixed_synapse_words]; // VLA
//!     control_t plastic_control_data[n_plastic_controls]; // VLA
//! }
//! ~~~~~~
//!
//! The relevant implementation structures are:
//! * ::synapse_row_plastic_part_t
//! * ::synapse_row_fixed_part_t
//! * ::single_synaptic_row_t
typedef struct synaptic_row *synaptic_row_t;

//! The type of an input
typedef REAL input_t;

//! The type of a state variable
typedef REAL state_t;

#endif /* __NEURON_TYPEDEFS_H__ */
