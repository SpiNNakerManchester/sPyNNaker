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

#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>
#include <spin1_api.h>

bool spike_processing_initialise(
        size_t row_max_n_bytes, uint mc_packet_callback_priority,
        uint user_event_priority, uint incoming_spike_buffer_size);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows(void);

//! \brief set the number of times spike_processing has to attempt rewiring
//! \return bool: currently, always true
bool spike_processing_do_rewiring(int number_of_rew);

#endif // _SPIKE_PROCESSING_H_
