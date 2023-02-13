/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
