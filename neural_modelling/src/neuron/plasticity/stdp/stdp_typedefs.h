/*
 * Copyright (c) 2014 The University of Manchester
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

//! \dir
//! \brief Spike Timing Dependent Plasticity (STDP)
//! \file
//! \brief Basic definitions for STDP
#ifndef _STDP_TYPEDEFS_H_
#define _STDP_TYPEDEFS_H_

//---------------------------------------
// Macros
//---------------------------------------
// Fixed-point number system used STDP
//! Position of the point in the fixed point math used by STDP
#define STDP_FIXED_POINT 11
//! The number 1.0 in the fixed point math used by STDP
#define STDP_FIXED_POINT_ONE    (1 << STDP_FIXED_POINT)

// Helper macros for 16-bit fixed-point multiplication
//! \brief Multiply two STDP fixed point numbers
//! \param[in] a: The first multiplicand
//! \param[in] b: The second multiplicand
//! \return The product
#define STDP_FIXED_MUL_16X16(a, b) maths_fixed_mul16(a, b, STDP_FIXED_POINT)

#define PRINT_PLASTICITY 0
//! The amount of right shift required to take a weight from s1615 format
//! to STDP_FIXED_POINT format (s4,11)
#define S1615_TO_STDP_RIGHT_SHIFT 4

//! \brief Multiply an accum by an STDP fixed point and return an accum
static inline accum mul_accum_fixed(accum a, int32_t stdp_fixed) {
    return a * kbits(stdp_fixed << S1615_TO_STDP_RIGHT_SHIFT);
}

#endif  // _STDP_TYPEDEFS_H_
