/*
 * Copyright (c) 2021 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
//! \file
//! \brief Defines the "local-only" processing of spikes, that is, the
//!        processing of spikes without using transfers from SDRAM
#ifndef __LOCAL_ONLY_H__
#define __LOCAL_ONLY_H__

#include <common/neuron-typedefs.h>

//: Provenance data for local-only processing
struct local_only_provenance {
	//! The maximum number of spikes received in a time step
    uint32_t max_spikes_received_per_timestep;
    //! The number of spikes dropped due to running out of time in a time step
    uint32_t n_spikes_dropped;
    //! The number of spikes dropped due to the queue having no space
    uint32_t n_spikes_lost_from_input;
    //! The maximum size of the spike input queue at any time
    uint32_t max_input_buffer_size;
};

/**
 * \brief Set up local-only processing of spikes.
 * \param[in] local_only_addr The address from which to read common data
 * \param[in] local_only_params_addr The address from which to read
 *                                   implementation-specific data
 * \param[in] n_rec_regions_used The number of recording regions used before
 *                               here
 * \param[out] ring_buffers Pointer to the ring buffers that hold future inputs
 * \return Whether the set up was done or not
 */
bool local_only_initialise(void *local_only_addr, void *local_only_params_addr,
        uint32_t n_rec_regions_used, uint16_t **ring_buffers);

/**
 * \brief Clear the spikes for the last time step
 * \param[in] time The time step at which the request is asked
 */
void local_only_clear_input(uint32_t time);

/**
 * \brief Store provenance gathered during run.
 * \param[out] prov Pointer to the struct to store the provenance in
 */
void local_only_store_provenance(struct local_only_provenance *prov);

#endif
