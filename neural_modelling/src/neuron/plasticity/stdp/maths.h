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

#ifndef MATHS_H
#define MATHS_H

// Standard includes
#include <common/neuron-typedefs.h>
#include <spin1_api.h>

//---------------------------------------
// Macros
//---------------------------------------
#define MIN(X, Y)	((X) < (Y) ? (X) : (Y))
#define MAX(X, Y)	((X) > (Y) ? (X) : (Y))

typedef struct int16_lut {
    uint16_t size;
    uint16_t shift;
    int16_t values[];
} int16_lut;

//---------------------------------------
// Plasticity maths function inline implementation
//---------------------------------------
//! \brief Copy a Lookup Table from SDRAM to DTCM, updating the address
//! \param[in/out] address Pointer to the SDRAM address to copy from.  This is
//!                        updated to point to the space after the structure.
//! \return A pointer to the copied lookup table
static inline int16_lut *maths_copy_int16_lut(address_t *address) {
    int16_lut *sdram_lut = (int16_lut *) *address;
    uint32_t size = sizeof(int16_lut) + (sdram_lut->size * sizeof(int16_t));
    int16_lut *lut = spin1_malloc(size);
    if (lut == NULL) {
        log_error("Not enough space to allocate LUT.  Try reducing the timestep,"
            " the number of neurons per core, or the tau value");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(lut, sdram_lut, size);

    // Pad to number of words (+ 1 for size / shift header)
    const uint32_t num_words = (lut->size / 2) + (((lut->size & 1) != 0) ? 1 : 0);
    *address += num_words + 1;

    return lut;
}


//---------------------------------------
static inline int32_t maths_lut_exponential_decay(
        uint32_t time, const int16_lut *lut) {
    // Calculate lut index
    uint32_t lut_index = time >> lut->shift;

    // Return value from LUT
    return (lut_index < lut->size) ? lut->values[lut_index] : 0;
}

static inline int32_t maths_clamp_pot(int32_t x, uint32_t shift) {
    uint32_t y = x >> shift;
    if (y) {
        x = ~y >> (32 - shift);
    }

    return x;
}

//---------------------------------------
// **NOTE** this should 'encourage' GCC to insert SMULxy 16x16 multiply
static inline int32_t maths_mul_16x16(int16_t x, int16_t y) {
    return x * y;
}

//---------------------------------------
static inline int32_t maths_fixed_mul16(
        int32_t a, int32_t b, const int32_t fixed_point_position) {
    // Multiply lower 16-bits of a and b together
    int32_t mul = __smulbb(a, b);

    // Shift down
    return (mul >> fixed_point_position);
}

//---------------------------------------
static inline int32_t maths_fixed_mul32(
        int32_t a, int32_t b, const int32_t fixed_point_position) {
    int32_t mul = a * b;

    // Shift down and return
    return (mul >> fixed_point_position);
}

#endif // MATHS_H
