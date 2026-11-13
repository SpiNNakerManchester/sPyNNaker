/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 */

#ifndef _STDP_UPDATE_SCHEDULE_H_
#define _STDP_UPDATE_SCHEDULE_H_

#include <stdbool.h>
#include <stdint.h>

//! One active row; kept in per-core SDRAM, separate from the synaptic matrix.
typedef struct {
    uint32_t address;       //!< System address of the synaptic row
    uint32_t n_bytes;       //!< Size of the row to transfer
    uint32_t colour_mask;   //!< Maximum age encoded in an incoming spike
    uint32_t cursor;        //!< Last simulation time written back for this row
} stdp_update_row_t;

//! Layout written by the host. Every synapse core owns a separate region.
typedef struct {
    uint32_t rows_per_timestep;
    uint32_t capacity;
    //! Hash table, active rows, per-neuron pressure state, then target links.
    uint32_t data[];
} stdp_update_region_t;

//! A proposed cursor change; publish it only after writing the row back.
typedef struct {
    stdp_update_row_t *row;
    uint32_t time;
    bool without_spike;
    bool under_pressure;
} stdp_update_commit_t;

typedef struct {
    uint32_t completed;
    uint32_t history_gaps;
    uint32_t out_of_order_spikes;
    uint32_t pressure_updates;
} stdp_update_provenance_t;

extern stdp_update_provenance_t stdp_update_provenance;

//! Initialise the optional scheduler. A null region leaves it disabled.
bool stdp_updates_initialise(
        stdp_update_region_t *region, uint32_t n_neurons,
        uint32_t index_mask, uint32_t post_delay_mask,
        uint32_t post_delay_shift);

//! Discard per-run state when the simulation is reset.
void stdp_updates_reset(void);

//! Whether there is a scheduler on this core.
extern bool stdp_updates_enabled;

//! Find or register a plastic row observed in the normal input path.
//! Returns null if there is no space for another row.
stdp_update_row_t *stdp_updates_get_row(
        uint32_t address, uint32_t n_bytes, uint32_t colour_mask,
        uint32_t initial_cursor, const uint16_t *controls, uint32_t n_controls);

//! Mark the oldest few events in a near-full post history as at risk.
void stdp_updates_note_pressure(
        uint32_t neuron, uint32_t oldest, uint32_t latest_at_risk);

//! Grant a bounded amount of background work for this timestep.
void stdp_updates_begin_timestep(uint32_t time);

//! Prefer rows with an unprocessed post event at risk of eviction, then
//! continue the normal sweep. A pressure sweep keeps its place between ticks.
stdp_update_commit_t stdp_updates_next(uint32_t time);

//! Commit the cursor of a completed write. A null row has no cursor.
static inline void stdp_updates_commit(stdp_update_commit_t update) {
    if (update.row != 0) {
        update.row->cursor = update.time;
        stdp_update_provenance.completed += update.without_spike;
        stdp_update_provenance.pressure_updates += update.under_pressure;
    }
}

#endif
