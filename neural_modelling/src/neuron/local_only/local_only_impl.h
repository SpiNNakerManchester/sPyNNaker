/*
 * Copyright (c) The University of Sussex, Garibaldi Pineda Garcia
 * James Turner, James Knight and Thomas Nowotny
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

#ifndef _LOCAL_ONLY_H_
#define _LOCAL_ONLY_H_

#include <common/neuron-typedefs.h>

extern uint32_t synapse_delay_mask;

extern uint32_t synapse_type_index_bits;

extern uint32_t synapse_index_bits;

//! \brief Load the data required
//! \return Whether the loading was successful or not
bool local_only_impl_initialise(void *address);

//! \brief Process a spike received
void local_only_impl_process_spike(uint32_t time, uint32_t spike,
        uint16_t* ring_buffers);

#endif
