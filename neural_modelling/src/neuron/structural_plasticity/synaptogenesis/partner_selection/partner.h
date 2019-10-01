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

#ifndef _PARTNER_SELECTION_H_
#define _PARTNER_SELECTION_H_

#include <neuron/synapses.h>

// MARS KISS 64 (RNG)
#include <random.h>
// Bit manipulation after RNG
#include <stdfix-full-iso.h>

#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>

// value to be returned when there is no valid partner selection
#define INVALID_SELECTION ((spike_t) - 1)

void partner_init(uint8_t **data);

static inline void partner_spike_received(uint32_t time, spike_t spike);

static inline bool potential_presynaptic_partner(
        uint32_t time, uint32_t* population_id, uint32_t *sub_population_id,
        uint32_t *neuron_id, spike_t *spike, uint32_t *m_pop_index);

#endif // _PARTNER_H_
