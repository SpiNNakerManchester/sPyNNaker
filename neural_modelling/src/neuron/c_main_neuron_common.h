/*
 * Copyright (c) 2017-2020 The University of Manchester
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
#include <stdbool.h>
#include <stdint.h>

#include <data_specification.h>
#include <tdma_processing.h>

#include "neuron.h"

//! The provenance information provided by neurons
struct neuron_provenance {
    //! The current time.
    uint32_t current_timer_tick;
    //! The number of times a TDMA slot was missed
    uint32_t n_tdma_mises;
    //! Earliest send time within any time step
    uint32_t earliest_send;
    //! Latest send time within any time step
    uint32_t latest_send;
};

//! The region IDs used by the neuron processing
struct neuron_regions {
    //! The core parameters
    uint32_t core_params;
    //! The neuron parameters
    uint32_t neuron_params;
    //! The current source parameters
    uint32_t current_source_params;
    //! The neuron recording details
    uint32_t neuron_recording;
};

//! Declare that time exists
extern uint32_t time;

//! Latest time in a timestep that any neuron has sent a spike
extern uint32_t latest_send_time;

//! Earliest time in a timestep that any neuron has sent a spike
extern uint32_t earliest_send_time;

//! \brief Callback to store neuron provenance data (format: neuron_provenance).
//! \param[out] prov: The data structure to store provenance data in
static inline void store_neuron_provenance(struct neuron_provenance *prov) {
    prov->current_timer_tick = time;
    prov->n_tdma_mises = tdma_processing_times_behind();
    prov->earliest_send = earliest_send_time;
    prov->latest_send = latest_send_time;
}

//! \brief Read data to set up neuron processing
//! \param[in] ds_regions: Pointer to region position data
//! \param[in] regions: The indices of the regions to be read
//! \param[out] n_rec_regions_used: The number of recording regions used
//! \return a boolean indicating success (True) or failure (False)
static inline bool initialise_neuron_regions(
        data_specification_metadata_t *ds_regions,
        struct neuron_regions regions, uint32_t *n_rec_regions_used) {

    // Set up the neurons
    if (!neuron_initialise(
            data_specification_get_region(regions.core_params, ds_regions),
            data_specification_get_region(regions.neuron_params, ds_regions),
            data_specification_get_region(regions.current_source_params, ds_regions),
            data_specification_get_region(regions.neuron_recording, ds_regions),
            n_rec_regions_used)) {
        return false;
    }

    return true;
}
