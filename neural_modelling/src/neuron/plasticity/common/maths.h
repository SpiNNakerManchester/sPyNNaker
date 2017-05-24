#ifndef MATHS_H
#define MATHS_H

// Standard includes
#include "../../../common/neuron-typedefs.h"

//---------------------------------------
// Macros
//---------------------------------------
#define MIN(X, Y)	((X) < (Y) ? (X) : (Y))
#define MAX(X, Y)	((X) > (Y) ? (X) : (Y))

//---------------------------------------
// Plasticity maths function inline implementation
//---------------------------------------
static inline address_t maths_copy_int16_lut(
       address_t start_address, uint32_t num_entries, int16_t *lut) {

    // Pad to number of words
    const uint32_t num_words = (num_entries / 2)
                               + (((num_entries & 1) != 0) ? 1 : 0);

    // Copy entries to LUT
    spin1_memcpy(lut, start_address, sizeof(int16_t) * num_entries);

    // Return address after words
    return start_address + num_words;
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
static inline int32_t maths_lut_exponential_decay(
        uint32_t time, const uint32_t time_shift, const uint32_t lut_size,
        const int16_t *lut) {

    // Calculate lut index
    uint32_t lut_index = time >> time_shift;

    // Return value from LUT
    return (lut_index < lut_size) ? lut[lut_index] : 0;
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
