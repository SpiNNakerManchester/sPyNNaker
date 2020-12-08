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
    uint32_t n_tdma_mises;
};

struct neuron_regions {
    uint32_t neuron_params;
    uint32_t neuron_recording;
};

//! Declare that time exists
extern uint32_t time;

//! \brief Callback to store neuron provenance data (format: neuron_provenance).
//! \param[out] prov: The data structure to store provenance data in
static inline void store_neuron_provenance(struct neuron_provenance *prov) {
    prov->current_timer_tick = time;
    prov->n_tdma_mises = tdma_processing_times_behind();
}

static inline bool initialise_neuron_regions(
        data_specification_metadata_t *ds_regions,
        struct neuron_regions regions, uint32_t *n_rec_regions_used) {

    // Set up the neurons
    if (!neuron_initialise(
            data_specification_get_region(regions.neuron_params, ds_regions),
            data_specification_get_region(regions.neuron_recording, ds_regions),
            n_rec_regions_used)) {
        return false;
    }

    return true;
}
