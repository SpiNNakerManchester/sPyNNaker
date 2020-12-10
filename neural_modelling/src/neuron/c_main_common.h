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
#include <simulation.h>
#include <profiler.h>
#include <recording.h>

/* validates that the model being compiled does indeed contain a application
 * magic number*/
#ifndef APPLICATION_NAME_HASH
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
    constant
#endif

struct common_regions {
    uint32_t system;
    uint32_t provenance;
    uint32_t profiler;
    uint32_t recording;
};

struct common_priorities {
    uint32_t sdp;
    uint32_t dma;
    uint32_t timer;
};

static inline bool initialise_common_regions(
        uint32_t *timer_period, uint32_t *simulation_ticks,
        uint32_t *infinite_run, uint32_t *time, uint32_t *recording_flags,
        prov_callback_t store_provenance_function, callback_t timer_callback,
        struct common_regions regions, struct common_priorities priorities,
        data_specification_metadata_t **ds_regions) {

    // Get the address this core's DTCM data starts at from SRAM
    *ds_regions = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(*ds_regions)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(regions.system, *ds_regions),
            APPLICATION_NAME_HASH, timer_period, simulation_ticks,
            infinite_run, time, priorities.sdp, priorities.dma)) {
        return false;
    }
    simulation_set_provenance_function(
        store_provenance_function,
        data_specification_get_region(regions.provenance, *ds_regions));

    // Setup profiler
    profiler_init(data_specification_get_region(regions.profiler, *ds_regions));

    // Setup recording
    void *rec_addr = data_specification_get_region(regions.recording, *ds_regions);
    if (!recording_initialize(&rec_addr, recording_flags)) {
        return false;
    }

    // Set timer tick (in microseconds)
    log_debug("setting timer tick callback for %d microseconds", *timer_period);
    spin1_set_timer_tick(*timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, priorities.timer);

    return true;
}

static inline void common_pause(uint32_t recording_flags) {

    // Finalise any recordings that are in progress
    if (recording_flags > 0) {
        log_debug("updating recording regions");
        recording_finalise();
    }

    profiler_finalise();
}
