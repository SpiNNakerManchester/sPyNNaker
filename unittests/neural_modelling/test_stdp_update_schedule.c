/*
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

#include <assert.h>
#include <stdlib.h>

#include "stdp_update_schedule.h"

static stdp_update_region_t *make_region(uint32_t capacity, uint32_t budget,
        uint32_t neurons) {
    stdp_update_region_t *region = calloc(1, sizeof(*region) +
            capacity * (sizeof(stdp_update_row_t) + 2 * sizeof(uint16_t)) +
            16 * neurons + 6 * capacity * neurons);
    assert(region != NULL);
    region->capacity = capacity;
    region->rows_per_timestep = budget;
    return region;
}

static void test_pressure(void) {
    stdp_update_region_t *region = make_region(4, 1, 4);
    assert(stdp_updates_initialise(region, 4, 3, 15, 2));
    const uint16_t other = 2;
    const uint16_t serviced = 1;
    const uint16_t shared[] = {1 | (1 << 2), 1 | (4 << 2)};
    stdp_update_row_t *a = stdp_updates_get_row(
            0x70001000, 20, 0, 1, &other, 1);
    stdp_update_row_t *d = stdp_updates_get_row(
            0x70001050, 20, 0, 10, &serviced, 1);
    stdp_update_row_t *c = stdp_updates_get_row(
            0x70001028, 20, 0, 1, &other, 1);
    stdp_update_row_t *b = stdp_updates_get_row(
            0x70001014, 20, 15, 1, shared, 2);
    assert(a != NULL && b != NULL && c != NULL && d != NULL);

    stdp_updates_note_pressure(1, 6, 6);
    stdp_updates_begin_timestep(22);
    // At cutoff 6 the earliest delayed event (at 7) is not ready.
    stdp_update_commit_t update = stdp_updates_next(22);
    assert(update.row == a && !update.under_pressure);
    stdp_updates_commit(update);
    assert(stdp_updates_next(22).row == NULL);

    stdp_updates_begin_timestep(23);
    update = stdp_updates_next(23);
    // B jumps ahead of C, even though only its shorter delay is safe.
    assert(update.row == b && update.time == 7 && update.under_pressure);
    assert(b->cursor == 1 && stdp_update_provenance.pressure_updates == 0);
    stdp_updates_commit(update);
    assert(b->cursor == 7 && stdp_update_provenance.pressure_updates == 1);
    assert(stdp_updates_next(23).row == NULL);

    // A new urgent request does not consume the reserved periodic turn.
    stdp_updates_note_pressure(1, 6, 6);
    stdp_updates_begin_timestep(24);
    update = stdp_updates_next(24);
    assert(update.row == d && !update.under_pressure);
    stdp_updates_commit(update);

    // Without another notification, the later delay remains pending.
    stdp_updates_begin_timestep(25);
    update = stdp_updates_next(25);
    assert(update.row == c && !update.under_pressure);
    stdp_updates_commit(update);
    stdp_updates_begin_timestep(26);
    update = stdp_updates_next(26);
    assert(update.row == b && update.time == 10 && update.under_pressure);
    stdp_updates_commit(update);
    assert(stdp_update_provenance.pressure_updates == 2);

    stdp_updates_reset();
    a = stdp_updates_get_row(0x70001000, 20, 0, 1, &other, 1);
    stdp_updates_begin_timestep(30);
    update = stdp_updates_next(30);
    assert(update.row == a && !update.under_pressure);
    stdp_updates_commit(update);

    // A pause on the tick reserved for the normal sweep must not leave
    // a stale reservation on a later timestep after resume.
    stdp_updates_note_pressure(2, 30, 30);
    stdp_updates_begin_timestep(32);
    update = stdp_updates_next(32);
    assert(update.row == a && update.under_pressure);
    stdp_updates_commit(update);
    stdp_updates_note_pressure(2, 33, 33);
    stdp_updates_begin_timestep(35);
    update = stdp_updates_next(35);
    assert(update.row == a && update.under_pressure);
    free(region);
}

static void test_reverse_index(void) {
    stdp_update_region_t *region = make_region(32, 3, 4);
    assert(stdp_updates_initialise(region, 4, 3, 0, 2));
    const uint16_t quiet = 2;
    stdp_update_row_t *first = NULL;
    for (uint32_t i = 0; i < 24; i++) {
        stdp_update_row_t *row = stdp_updates_get_row(
                0x70001000 + i * 64, 64, 0, 1, &quiet, 1);
        assert(row != NULL);
        if (i == 0) {
            first = row;
        }
    }

    // Pressure can be raised before any row to that neuron registers.
    // Repeated controls must not create a second link for the same row.
    stdp_updates_note_pressure(0, 6, 8);
    const uint16_t hot_a[] = {0, 0};
    const uint16_t hot_b = 1;
    stdp_update_row_t *a = stdp_updates_get_row(
            0x70002000, 64, 0, 7, hot_a, 2);
    stdp_update_row_t *b = stdp_updates_get_row(
            0x70002040, 64, 0, 1, &hot_b, 1);
    stdp_update_row_t *c = stdp_updates_get_row(
            0x70002080, 64, 0, 1, hot_a, 2);
    assert(a != NULL && b != NULL && c != NULL);
    stdp_updates_note_pressure(1, 6, 6);
    stdp_updates_begin_timestep(10);

    // The two affected neurons take turns; the 24 unrelated rows do not
    // consume pressure checks. Leave one slot for the ordinary sweep.
    stdp_update_commit_t update = stdp_updates_next(10);
    assert(update.row == a && update.under_pressure);
    stdp_updates_commit(update);
    update = stdp_updates_next(10);
    assert(update.row == b && update.under_pressure);
    // Leave this write uncommitted to exercise a retry on the next tick.
    update = stdp_updates_next(10);
    assert(update.row == first && !update.under_pressure);
    stdp_updates_commit(update);
    assert(stdp_updates_next(10).row == NULL);

    stdp_updates_begin_timestep(11);
    update = stdp_updates_next(11);
    assert(update.row == c && update.under_pressure);
    stdp_updates_commit(update);
    update = stdp_updates_next(11);
    assert(update.row == b && update.under_pressure);
    stdp_updates_commit(update);
    assert(stdp_update_provenance.pressure_updates == 3);
    free(region);
}

int main(void) {
    assert(stdp_updates_initialise(NULL, 0, 0, 0, 0));
    stdp_updates_begin_timestep(20);
    assert(stdp_updates_next(20).row == NULL);

    enum { CAPACITY = 4 };
    stdp_update_region_t *region = make_region(CAPACITY, 2, 1);
    region->capacity = 3;
    assert(!stdp_updates_initialise(region, 1, 0, 0, 0));
    region->capacity = CAPACITY;
    assert(stdp_updates_initialise(region, 1, 0, 0, 0));

    stdp_update_row_t *a = stdp_updates_get_row(0x70001000, 20, 15, 1, NULL, 0);
    stdp_update_row_t *b = stdp_updates_get_row(0x70001014, 20, 0, 1, NULL, 0);
    stdp_update_row_t *c = stdp_updates_get_row(0x70001028, 20, 0, 2, NULL, 0);
    assert(a && b && c && a != b && b != c);

    // A is too young for its 4-bit colour, and still consumes one of the
    // two row checks. B can update but must not change until writeback.
    stdp_updates_begin_timestep(10);
    stdp_update_commit_t update = stdp_updates_next(10);
    assert(update.row == b && update.time == 9 && update.without_spike);
    assert(b->cursor == 1 && stdp_update_provenance.completed == 0);
    stdp_updates_commit(update);
    assert(b->cursor == 9 && stdp_update_provenance.completed == 1);
    assert(stdp_updates_next(10).row == NULL);

    // The next timestep continues at C; A's cutoff leaves the oldest
    // timestamp an arriving real spike could carry out of the update.
    stdp_updates_begin_timestep(20);
    update = stdp_updates_next(20);
    assert(update.row == c && update.time == 19);
    stdp_updates_commit(update);
    assert(stdp_updates_next(21).row == NULL);
    update = stdp_updates_next(20);
    assert(update.row == a && update.time == 4);
    stdp_updates_commit(update);
    assert(stdp_updates_get_row(a->address, 20, 15, 1, NULL, 0) == a);
    assert(a->cursor == 4);
    assert(stdp_updates_get_row(a->address, 20, 7, 1, NULL, 0) == NULL);

    // Exhaustion cannot evict a live cursor.
    assert(stdp_updates_get_row(0x7000103c, 20, 0, 1, NULL, 0) != NULL);
    assert(stdp_updates_get_row(0x70001050, 20, 0, 1, NULL, 0) == NULL);
    assert(a->cursor == 4);

    // A real spike can advance a cursor without counting as a no-spike
    // update. Reset removes all old registrations and their cursors.
    stdp_updates_commit((stdp_update_commit_t) {.row = a, .time = 6});
    assert(a->cursor == 6 && stdp_update_provenance.completed == 3);
    stdp_updates_reset();
    stdp_updates_begin_timestep(1);
    assert(stdp_updates_next(1).row == NULL);
    assert(stdp_update_provenance.completed == 0);
    a = stdp_updates_get_row(0x70001000, 20, 0, 0, NULL, 0);
    assert(a != NULL && a->cursor == 0);

    free(region);
    test_pressure();
    test_reverse_index();
    return 0;
}
