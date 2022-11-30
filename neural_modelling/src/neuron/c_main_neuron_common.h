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
#include <debug.h>

#include <data_specification.h>

#include "neuron.h"

uint64_t udiv64(uint64_t num, uint64_t den) {

    uint64_t quot = 0;
    uint64_t qbit = 1;

    if (den == 0) {
        /* Intentional divide by zero, without
	       triggering a compiler warning which
	       would abort the build */
        return 1/((unsigned)den);
    }

    /* Left-justify denominator and count shift */
    while ((int64_t) den >= 0) {
        den <<= 1;
        qbit <<= 1;
    }

    while (qbit) {
        if (den <= num) {
            num -= den;
            quot += qbit;
        }
        den >>= 1;
        qbit >>= 1;
    }
    return quot;
}

//! The provenance information provided by neurons
struct neuron_provenance {
    //! The current time.
    uint32_t current_timer_tick;
    //! The number of times a TDMA slot was missed
    uint32_t n_tdma_misses;
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
    //! The initial values at time 0
    uint32_t initial_values;
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
    prov->n_tdma_misses = 0;
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
			data_specification_get_region(regions.initial_values, ds_regions),
            n_rec_regions_used)) {
        return false;
    }

    return true;
}
