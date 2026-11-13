/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 */

#include "stdp_update_schedule.h"
#include <stddef.h>
#include <string.h>

#define NONE UINT16_MAX
#define NO_EVENT UINT32_MAX
#define MAX_CAPACITY 16384

// One reverse link per distinct (active row, post neuron) pair. The
// extrema allow a short delay to be processed while a longer one waits.
typedef struct {
    uint16_t next_row;
    uint16_t first_delay;
    uint16_t last_delay;
} stdp_update_target_t;

typedef struct {
    uint32_t oldest;
    uint32_t lookahead;
    uint16_t first_row;
    uint16_t pending_row;
    uint16_t next_post;
    bool rescan;
} stdp_update_post_t;

typedef struct {
    uint16_t head;
    uint16_t tail;
} pressure_queue_t;

bool stdp_updates_enabled;
stdp_update_provenance_t stdp_update_provenance;
static stdp_update_region_t *config;
static uint16_t *hash_table;
static stdp_update_row_t *rows;
static stdp_update_post_t *posts;
static stdp_update_target_t *targets;
static uint32_t table_size;
static uint32_t hash_shift;
static uint32_t n_posts;
static uint32_t target_index_mask;
static uint32_t target_delay_mask;
static uint32_t target_delay_shift;

static uint32_t n_active;
static uint32_t next_row;
static uint32_t remaining;
static uint32_t scheduled_tick;
static uint32_t next_periodic_tick;
static uint32_t pressure_checks;
static bool periodic_tick_required;
static pressure_queue_t ready;
static pressure_queue_t deferred;

void stdp_updates_reset(void) {
    if (!stdp_updates_enabled) {
        return;
    }
    n_active = 0;
    remaining = 0;
    next_row = 0;
    ready = (pressure_queue_t) {NONE, NONE};
    deferred = ready;
    periodic_tick_required = false;
    stdp_update_provenance = (stdp_update_provenance_t) {0};
    memset(hash_table, 0xff, table_size * sizeof(*hash_table));
    for (uint32_t i = 0; i < n_posts; i++) {
        posts[i].oldest = NO_EVENT;
        posts[i].first_row = NONE;
        posts[i].pending_row = NONE;
    }
}

bool stdp_updates_initialise(
        stdp_update_region_t *region, uint32_t n_neurons,
        uint32_t index_mask, uint32_t post_delay_mask,
        uint32_t post_delay_shift) {
    stdp_updates_enabled = false;
    if (region == NULL) {
        return true;
    }
    uint32_t capacity = region->capacity;
    if (capacity == 0 || capacity > MAX_CAPACITY ||
            (capacity & (capacity - 1)) != 0 ||
            region->rows_per_timestep == 0 ||
            region->rows_per_timestep > capacity || n_neurons == 0 ||
            n_neurons >= NONE || post_delay_mask > UINT16_MAX ||
            post_delay_shift >= 32) {
        return false;
    }

    // Leave at least half the hash slots empty; store the rows densely in
    // registration order so the normal sweep never scans empty slots.
    config = region;
    table_size = 2 * capacity;
    hash_shift = (uint32_t) __builtin_clz(table_size - 1);
    n_posts = n_neurons;
    target_index_mask = index_mask;
    target_delay_mask = post_delay_mask;
    target_delay_shift = post_delay_shift;
    hash_table = (void *) region->data;
    rows = (void *) &hash_table[table_size];
    posts = (void *) &rows[capacity];
    targets = (void *) &posts[n_posts];
    stdp_updates_enabled = true;
    stdp_updates_reset();
    return true;
}

static inline void enqueue(pressure_queue_t *queue, uint32_t neuron) {
    if (queue->head == NONE) {
        queue->head = neuron;
    } else {
        posts[queue->tail].next_post = neuron;
    }
    queue->tail = neuron;
    posts[neuron].next_post = NONE;
}

static inline void schedule_pressure(uint32_t neuron, stdp_update_post_t *post) {
    if (post->pending_row == NONE) {
        post->pending_row = post->first_row;
        post->rescan = false;
        enqueue(&ready, neuron);
    } else {
        // Earlier links in the current sweep may need another look.
        post->rescan = true;
    }
}

stdp_update_row_t *stdp_updates_get_row(
        uint32_t address, uint32_t n_bytes, uint32_t colour_mask,
        uint32_t initial_cursor, const uint16_t *controls, uint32_t n_controls) {
    if (!stdp_updates_enabled || address == 0) {
        return NULL;
    }
    uint32_t slot = ((address >> 2) * UINT32_C(2654435761)) >> hash_shift;
    while (hash_table[slot] != NONE) {
        stdp_update_row_t *row = &rows[hash_table[slot]];
        if (row->address == address) {
            if (row->n_bytes != n_bytes || row->colour_mask != colour_mask) {
                return NULL;
            }
            return row;
        }
        slot = (slot + 1) & (table_size - 1);
    }
    if (n_active == config->capacity) {
        return NULL;
    }
    for (uint32_t i = 0; i < n_controls; i++) {
        if ((controls[i] & target_index_mask) >= n_posts) {
            return NULL;
        }
    }

    // Build the index only on first registration. Repeated controls for
    // the same neuron share one link. Untouched target slots are never read.
    uint32_t index = n_active;
    stdp_update_target_t *row_targets = &targets[index * n_posts];
    for (uint32_t i = 0; i < n_controls; i++) {
        uint32_t control = controls[i];
        uint32_t neuron = control & target_index_mask;
        uint32_t delay = (control >> target_delay_shift) & target_delay_mask;
        stdp_update_post_t *post = &posts[neuron];
        stdp_update_target_t *target = &row_targets[neuron];
        if (post->first_row != index) {
            *target = (stdp_update_target_t) {post->first_row, delay, delay};
            post->first_row = index;
            if (post->oldest != NO_EVENT) {
                schedule_pressure(neuron, post);
            }
        } else {
            if (delay < target->first_delay) {
                target->first_delay = delay;
            }
            if (delay > target->last_delay) {
                target->last_delay = delay;
            }
        }
    }

    stdp_update_row_t *row = &rows[index];
    *row = (stdp_update_row_t) {address, n_bytes, colour_mask, initial_cursor};
    hash_table[slot] = index;
    n_active++;
    return row;
}

void stdp_updates_note_pressure(
        uint32_t neuron, uint32_t oldest, uint32_t latest_at_risk) {
    if (!stdp_updates_enabled || neuron >= n_posts) {
        return;
    }
    stdp_update_post_t *post = &posts[neuron];
    if (post->oldest == oldest && post->lookahead == latest_at_risk) {
        return;
    }
    post->oldest = oldest;
    post->lookahead = latest_at_risk;
    if (post->first_row != NONE) {
        schedule_pressure(neuron, post);
    }
}

void stdp_updates_begin_timestep(uint32_t time) {
    if (!stdp_updates_enabled) {
        return;
    }
    remaining = n_active < config->rows_per_timestep
            ? n_active : config->rows_per_timestep;
    scheduled_tick = time;
    if (deferred.head != NONE) {
        if (ready.head == NONE) {
            ready = deferred;
        } else {
            posts[ready.tail].next_post = deferred.head;
            ready.tail = deferred.tail;
        }
        deferred.head = NONE;
    }
    // Bound index traversal as well as DMA work, and leave time for the
    // periodic sweep even if histories stay full.
    pressure_checks = 4 * remaining;
    if (periodic_tick_required && time == next_periodic_tick) {
        pressure_checks = 0;
    }
    periodic_tick_required = false;
}

static inline uint32_t row_cutoff(const stdp_update_row_t *row, uint32_t time) {
    // A packet can carry a timestamp as early as time - colour_mask.
    // Leave that entire tick to real spikes.
    return time > row->colour_mask ? time - row->colour_mask - 1 : 0;
}

// Bound the delayed times for the oldest events. The row update applies
// each connection's exact delay and never goes past the safe cutoff.
static inline bool post_event_due(uint32_t cursor, uint32_t cutoff,
        const stdp_update_post_t *post, const stdp_update_target_t *target) {
    if (cutoff <= cursor || cutoff < post->oldest) {
        return false;
    }
    if (target->first_delay <= cutoff - post->oldest &&
            (cursor < post->lookahead ||
            target->first_delay > cursor - post->lookahead)) {
        return true;
    }
    return target->last_delay <= cutoff - post->oldest;
}

stdp_update_commit_t stdp_updates_next(uint32_t time) {
    if (!stdp_updates_enabled || time != scheduled_tick || remaining == 0) {
        return (stdp_update_commit_t) {0};
    }
    while (ready.head != NONE && pressure_checks != 0) {
        uint32_t neuron = ready.head;
        stdp_update_post_t *post = &posts[neuron];
        ready.head = post->next_post;
        uint32_t index = post->pending_row;
        const stdp_update_target_t *target = &targets[index * n_posts + neuron];
        stdp_update_row_t *row = &rows[index];
        uint32_t cutoff = row_cutoff(row, time);
        uint32_t latest = post->lookahead;
        bool due = false;
        if (row->cursor < latest || target->last_delay > row->cursor - latest) {
            due = post_event_due(row->cursor, cutoff, post, target);
            // Revisit if part of the window isn't safe yet, or if the
            // proposed write gets cancelled before its cursor commits.
            post->rescan = true;
        }

        // Round robin between neurons as well as between their linked rows.
        // Do not repeat a sweep of the same links within this tick.
        post->pending_row = target->next_row;
        if (post->pending_row != NONE) {
            enqueue(&ready, neuron);
        } else if (post->rescan) {
            post->pending_row = post->first_row;
            post->rescan = false;
            enqueue(&deferred, neuron);
        }
        pressure_checks--;
        if (due) {
            remaining--;
            if (remaining == 1) {
                pressure_checks = 0;
            } else if (remaining == 0) {
                periodic_tick_required = true;
                next_periodic_tick = time + 1;
            }
            return (stdp_update_commit_t) {
                .row = row, .time = cutoff,
                .without_spike = true, .under_pressure = true
            };
        }
    }
    while (remaining != 0) {
        remaining--;
        stdp_update_row_t *row = &rows[next_row++];
        if (next_row == n_active) {
            next_row = 0;
        }
        uint32_t cutoff = row_cutoff(row, time);
        if (cutoff > row->cursor) {
            return (stdp_update_commit_t) {
                .row = row, .time = cutoff, .without_spike = true
            };
        }
    }
    return (stdp_update_commit_t) {0};
}
