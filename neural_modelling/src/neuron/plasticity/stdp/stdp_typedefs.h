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

#ifndef _STDP_TYPEDEFS_H_
#define _STDP_TYPEDEFS_H_

//---------------------------------------
// Macros
//---------------------------------------
// Fixed-point number system used STDP
#define STDP_FIXED_POINT 11
#define STDP_FIXED_POINT_ONE    (1 << STDP_FIXED_POINT)

// Helper macros for 16-bit fixed-point multiplication
#define STDP_FIXED_MUL_16X16(a, b) maths_fixed_mul16(a, b, STDP_FIXED_POINT)

#endif  // _STDP_TYPEDEFS_H_
