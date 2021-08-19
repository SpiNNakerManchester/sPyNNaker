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

//! \dir
//! \brief Partner selection rule
//! \file
//! \brief Partner selection rule common API
#ifndef _PARTNER_SELECTION_H_
#define _PARTNER_SELECTION_H_

#include <neuron/synapses.h>

// MARS KISS 64 (RNG)
#include <random.h>
// Bit manipulation after RNG
#include <stdfix-full-iso.h>

#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>

//! value to be returned when there is no valid partner selection
#define INVALID_SELECTION ((spike_t) - 1)

//! \brief Initialise the partner selection rule
//! \param[in,out] data: A variable holding the location in SDRAM to configure
//!     the rule from. Will be updated to point to the first location after the
//!     configuration data.
void partner_init(uint8_t **data);

//! \brief Notifies the rule that a spike has been received
//! \param[in] time: The time that the spike was received at
//! \param[in] spike:
//!     The spike that was received (includes the sending neuron ID)
static inline void partner_spike_received(uint32_t time, spike_t spike);

//! \brief Choose the potential (remote) synaptic partner
//! \param[in] time: The current time
//! \param[out] population_id: The ID of the other population
//! \param[out] sub_population_id: The ID of the subpopulation (corresponds to
//!     remote SpiNNaker core handling the population)
//! \param[out] neuron_id: The ID of the neuron within the subpopulation
//! \param[out] spike: The spike that made this a meaningful choice
//! \param[out] m_pop_index: The master population table index
//! \return True if a choice was made
static inline bool potential_presynaptic_partner(
        uint32_t time, uint32_t *restrict population_id,
        uint32_t *restrict sub_population_id,
        uint32_t *restrict neuron_id, spike_t *restrict spike,
        uint32_t *restrict m_pop_index);

#endif // _PARTNER_H_
