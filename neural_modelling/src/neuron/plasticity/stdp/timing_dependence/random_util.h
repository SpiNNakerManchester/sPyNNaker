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

#include <random.h>

static mars_kiss64_seed_t seed = {123456789, 234567891, 345678912, 456789123};

static inline int32_t mars_kiss_fixed_point(void) {
    return (int32_t) (mars_kiss64_seed(seed) & (STDP_FIXED_POINT_ONE - 1));
}
