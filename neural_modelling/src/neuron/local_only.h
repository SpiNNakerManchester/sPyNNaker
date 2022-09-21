/*
 * Copyright (c) 2021-2022 The University of Manchester
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
