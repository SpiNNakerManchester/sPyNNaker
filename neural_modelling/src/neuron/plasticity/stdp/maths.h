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
//! \brief Support functions for STDP
#ifndef MATHS_H
#define MATHS_H

// Standard includes
#include <common/neuron-typedefs.h>
#include <debug.h>
#include <spin1_api.h>

//---------------------------------------
// Macros
//---------------------------------------
//! \brief Minimum. Evaluates arguments twice
//! \param X: First value
//! \param Y: Second value
//! \return Minimum of two values
#define MIN(X, Y)	((X) < (Y) ? (X) : (Y))
//! \brief Maximum. Evaluates arguments twice
//! \param X: First value
//! \param Y: Second value
//! \return Maximum of two values
#define MAX(X, Y)	((X) > (Y) ? (X) : (Y))

//! \brief Lookup Table of 16-bit integers.
//!
//! Will be padded to a word boundary at the end.
typedef struct int16_lut {
    uint16_t size;    //!< Number of entries in table
    uint16_t shift;   //!< Mapping from time to table index
    int16_t values[]; //!< Table of actual values
} int16_lut;

//---------------------------------------
// Plasticity maths function inline implementation
//---------------------------------------
//! \brief Copy a Lookup Table from SDRAM to DTCM, updating the address
//! \param[in,out] address: Pointer to the SDRAM address to copy from.  This is
//!                         updated to point to the space after the structure.
//! \return A pointer to the copied lookup table, malloc'd in DTCM
static inline int16_lut *maths_copy_int16_lut(address_t *address) {
    int16_lut *sdram_lut = (int16_lut *) *address;
    uint32_t size = sizeof(int16_lut) + (sdram_lut->size * sizeof(int16_t));
    int16_lut *lut = spin1_malloc(size);
    log_info("lut size %d", size);
    if (lut == NULL) {
        log_error("Not enough space to allocate LUT.  Try reducing the timestep,"
            " the number of neurons per core, or the tau value; size = %u", size);
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(lut, sdram_lut, size);

    // Pad to number of words (+ 1 for size / shift header)
    const uint32_t num_words = (lut->size / 2) + (((lut->size & 1) != 0) ? 1 : 0);
    *address += num_words + 1;

    return lut;
}

//---------------------------------------
// Plasticity maths function inline implementation
//---------------------------------------
static inline address_t maths_copy_int16_lut_with_size(
        address_t start_address, uint32_t num_entries, int16_t *lut) {
    // Pad to number of words
    const uint32_t num_words =
            (num_entries / 2) + (((num_entries & 1) != 0) ? 1 : 0);

    // Copy entries to LUT
    spin1_memcpy(lut, start_address, sizeof(int16_t) * num_entries);

    // Return address after words
    return start_address + num_words;
}

//! \brief Get value from lookup table
//! \param[in] time: The time that we are mapping
//! \param[in] lut: The lookup table (result of maths_copy_int16_lut())
//! \return The value from the LUT, or zero if out of range
static inline int32_t maths_lut_exponential_decay(
        uint32_t time, const int16_lut *lut) {
    // Calculate lut index
    uint32_t lut_index = time >> lut->shift;

    // Return value from LUT
    return (lut_index < lut->size) ? lut->values[lut_index] : 0;
}

static inline int32_t maths_lut_exponential_decay_time_shifted(
        uint32_t time, const uint32_t time_shift, const uint32_t lut_size,
        const int16_t *lut) {
    // Calculate lut index
    uint32_t lut_index = time >> time_shift;

    // Return value from LUT
    return (lut_index < lut_size) ? lut[lut_index] : 0;
}

//! \brief Clamp to fit in number of bits
//! \param[in] x: The value to clamp
//! \param[in] shift: Width of the field to clamp the value to fit in
//! \return The clamped value
static inline int32_t maths_clamp_pot(int32_t x, uint32_t shift) {
    uint32_t y = x >> shift;
    if (y) {
        x = ~y >> (32 - shift);
    }

    return x;
}

//---------------------------------------
//! \brief multiply two 16-bit numbers to get a 32-bit number.
//!
//! **NOTE:** this should 'encourage' GCC to insert SMULxy 16x16 multiply
//!
//! \param[in] x: The first multiplicand
//! \param[in] y: The first multiplicand
//! \return The product
static inline int32_t maths_mul_16x16(int16_t x, int16_t y) {
    return x * y;
}

//---------------------------------------
//! \brief multiply two 16-bit fixed point numbers (encoded in int32_t)
//! \param[in] a: The first multiplicand
//! \param[in] b: The first multiplicand
//! \param[in] fixed_point_position: The location of the fixed point
//! \return The product
static inline int32_t maths_fixed_mul16(
        int32_t a, int32_t b, const int32_t fixed_point_position) {
    // Multiply lower 16-bits of a and b together
    return __smulbb(a, b) >> fixed_point_position;
}

//---------------------------------------
//! \brief multiply two 32-bit fixed point numbers (encoded in int32_t)
//! \param[in] a: The first multiplicand
//! \param[in] b: The first multiplicand
//! \param[in] fixed_point_position: The location of the fixed point
//! \return The product
static inline int32_t maths_fixed_mul32(
        int32_t a, int32_t b, const int32_t fixed_point_position) {
    int32_t mul = a * b;

    // Shift down and return
    return (mul >> fixed_point_position);
}

#endif // MATHS_H
