/*
 * Copyright (c) 2023 The University of Manchester
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
//! \brief Stochastic common code

static inline uint32_t stoc_exp_ceil_accum(UREAL value) {
	uint32_t bits = bitsuk(value);
	uint32_t integer = bits >> 16;
	uint32_t fraction = bits & 0xFFFF;
	if (fraction > 0) {
	    return integer + 1;
	}
	return integer;
}

//! The minimum value of tau that has the potential to reduce below 1 from
//! mulitplication by negative fractional power of 2 of 16 or less.  In other
//! words, if tau is bigger than this, no multiplication by fractional negative
//! powers of 2 will ever bring it below 1, so a probability of >=1 is guaranteed.
static const uint32_t MIN_TAU = 0x10B55;

//! \brief Calculates the probability as a uint32_t from 0 to 0xFFFFFFFF (which is 1)
static inline uint32_t get_probability(UREAL tau, REAL p) {

	if (p >= 0) {

		// If tau is already more than 1, it will never get smaller here,
		// so just immediately return a probability of "1"
		if (tau >= 1.0k) {
			return 0xFFFFFFFF;
		}

		// The amount of left shift that will result in a tau > 1 (where tau
		// is 16-bits integer, 16-bits fractional, and < 1.0k, so we expect
		// at least 16 leading zeros, thus this can only be >= 0).  Note a
		// a 1 at bit 16 means clz = 16, but we can shift 1 place before >= 1
		// so we subtract 15 from clz to get the right number.
	    uint32_t over_left_shift = __builtin_clz(bitsuk(tau)) - 15;

		// If tau is going to be shifted by this amount
		if (p >= over_left_shift) {
			return 0xFFFFFFFF;
		}

		// Shift left by integer part to perform power of 2
		uint64_t accumulator = ((uint64_t) bitsuk(tau)) << (bitsk(p) >> 15);
		uint32_t fract_bits = bitsk(p) & 0x7FFF;

		// Multiply in fractional powers for each non-zero fractional bits
		for (uint32_t i = 0; i < 15; i++) {
			uint32_t bit = (fract_bits >> (14 - i)) & 0x1;
			if (bit) {
				// Do a U1616 * U1616 multiply here, which is safe in 64-bits
				accumulator = (accumulator * fract_powers_2[i]) >> 16;

				// If we are >= 1, return now as won't get smaller
				if (accumulator >= bitsuk(1.0ulk)) {
					return 0xFFFFFFFF;
				}
			}
		}

	    // Multiply accumulated fraction (must be <= 1 here) by 0xFFFFFFFF
		// to get final answer
		return (uint32_t) ((accumulator * 0xFFFFFFFFL) >> 16);
	} else {
		// If tau is too big, we will never make it small enough with negative
		// powers, so just return probability of 1
		if (bitsuk(tau) > MIN_TAU) {
			return 0xFFFFFFFF;
		}

	    // Negative left shift = positive right shift; have to multiply here
		// as accum negating seems to fail!
		REAL val = p * REAL_CONST(-1);

		// The amount of right shift that will make the MSB of tau disappear,
		// and so the value will be 0.  The most number of leading zeros is 32,
		// so this is always >= 0.  If we have a bit in position 31 (a very big
		// tau), this clz = 0 so this is 32, which means we can shift by 32
		uint32_t over_right_shift = 32 - __builtin_clz(bitsuk(tau));

		// If p <= 0, tau can only get smaller through multiplication with
		// fractional powers, so there is no point in doing the calculation if
		// it will already be shifted out of range of an accum
		if (val >= over_right_shift) {
			return 0;
		}

		// Shift right by integer value to perform negative power of 2
		uint64_t accumulator = ((uint64_t) bitsuk(tau)) >> (bitsk(val) >> 15);
		uint32_t fract_bits = bitsk(val) & 0x7FFF;

		// Multiply in fractional powers for each non-zero fractional bits
		for (uint32_t i = 0; i < 15; i++) {
			uint32_t bit = (fract_bits >> (14 - i)) & 0x1;
			if (bit) {
				// Do a U1616 * U1616 multiply here
				accumulator = (accumulator * fract_powers_half[i]) >> 16;

				// If we have reached a value of 0, return
				if (accumulator == 0) {
					return 0;
				}
			}
		}

		// Multiply accumulated fraction (must be <= 1 here) by 0xFFFFFFFF
		// to get final answer
		return (uint32_t) ((accumulator * 0xFFFFFFFFL) >> 16);
	}
}
