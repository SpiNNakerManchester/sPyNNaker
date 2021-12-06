/*
 * Copyright (c) 2017-2021 The University of Manchester
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

#include <stdfix-full-iso.h>

typedef struct spike_holder_t {
	uint8_t spikes_a;
	uint8_t spikes_b;
	uint8_t spikes_c;
	uint8_t spikes_d;
} spike_holder_t;

static inline void spike_profiling_cache_and_flush_spike_holder(
		struct spike_holder_t* counter_spikes,
		struct spike_holder_t* cache_levels) {

	cache_levels->spikes_a = counter_spikes->spikes_a;
	cache_levels->spikes_b = counter_spikes->spikes_b;
	cache_levels->spikes_c = counter_spikes->spikes_c;
	cache_levels->spikes_d = counter_spikes->spikes_d;

	// zero counters
	counter_spikes->spikes_a = 0;
	counter_spikes->spikes_b = 0;
	counter_spikes->spikes_c = 0;
	counter_spikes->spikes_d = 0;
}

static inline void spike_profiling_add_count(uint32_t row_length,
		struct spike_holder_t* spike_counter) {

	uint32_t a = 0;
	uint32_t b = 1;
	uint32_t c = 5;

	if (row_length <= a) {
		spike_counter->spikes_a++;
	} else if (row_length > a && row_length <= b) {
		spike_counter->spikes_b++;
	} else if (row_length > b && row_length <= c) {
		spike_counter->spikes_c++;
	} else if (row_length > c) {
		spike_counter->spikes_d++;
	}
}

static inline int32_t spike_profiling_get_spike_holder_as_int(
        struct spike_holder_t spikes) {

	union {
		int32_t inty;
		struct spike_holder_t sh;
	} x;

	x.sh = spikes;

	return x.inty;
}

static inline accum spike_profiling_get_spike_holder_as_accum(
        struct spike_holder_t spikes) {
	union {
		accum acc;
		struct spike_holder_t sh;
	} x;
	x.sh = spikes;

	return x.acc;
}

static inline void spike_profiling_print_spikes_from_spike_holder(
        struct spike_holder_t spikes_orig) {
	io_printf(IO_BUF, "Spikes from input: a %u, b %u, c %u, d %u \n",
			spikes_orig.spikes_a, spikes_orig.spikes_b, spikes_orig.spikes_c,
			spikes_orig.spikes_d);
}

static inline void spike_profiling_print_spikes_from_int(int32_t output) {
	io_printf(IO_BUF, "Spikes from output: a %d, b %d, c %d, d %d \n",
			(output & 0xFF), (output >> 8 & 0xFF), (output >> 16 & 0xFF),
			(output >> 24 & 0xFF));
}
