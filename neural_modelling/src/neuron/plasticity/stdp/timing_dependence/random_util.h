/*
 * Copyright (c) 2017-2019 The University of Manchester
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
//! \brief Utility function for random number generation

//! \brief **YUCK** copy and pasted RNG to allow inlining and also to avoid
//!     horrific executable bloat.
//!
//! Algorithm is the KISS algorithm due to Marsaglia and Zaman. (Fortunately, we
//! don't do cryptography on SpiNNaker.)
//!
//! \return random number, uniformly distributed over range 0 ..
//!     2<sup>::STDP_FIXED_POINT_ONE</sup>
static inline int32_t mars_kiss_fixed_point(void) {
    // **YUCK** copy and pasted rng to allow inlining and also to avoid
    // horrific executable bloat

    /* Seed variables */
    static uint32_t x = 123456789;
    static uint32_t y = 234567891;
    static uint32_t z = 345678912;
    static uint32_t w = 456789123;
    static uint32_t c = 0;
    int32_t t;

    y ^= (y << 5);
    y ^= (y >> 7);
    y ^= (y << 22);
    t = z + w + c;
    z = w;
    c = t < 0;
    w = t & 2147483647;
    x += 1411392427;

    uint32_t random = x + y + w;

    // **YUCK** mask out and return STDP_FIXED_POINT_ONE lowest bits
    return (int32_t)(random & (STDP_FIXED_POINT_ONE - 1));
}
