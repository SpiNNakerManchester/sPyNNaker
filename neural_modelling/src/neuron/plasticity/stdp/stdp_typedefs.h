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

#define print_plasticity false  // true

//! The amount of right shift required to take a weight from s1615 format
//! to STDP_FIXED_POINT format (s4,11)
#define S1615_TO_STDP_RIGHT_SHIFT 4

//! \brief Multiply an accum by an STDP fixed point and return an accum
static inline accum mul_accum_fixed(accum a, int32_t stdp_fixed) {
    return a * kbits(stdp_fixed << S1615_TO_STDP_RIGHT_SHIFT);
}

#endif  // _STDP_TYPEDEFS_H_
