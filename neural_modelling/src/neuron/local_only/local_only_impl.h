/*
 * Copyright (c) 2019-2023 The University of Manchester
 * based on work Copyright (c) The University of Sussex,
 * Garibaldi Pineda Garcia, James Turner, James Knight and Thomas Nowotny
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
