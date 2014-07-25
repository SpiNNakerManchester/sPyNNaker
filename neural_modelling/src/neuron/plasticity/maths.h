#ifndef MATHS_H
#define MATHS_H

#include <stdint.h>

//---------------------------------------
// Macros
//---------------------------------------
#define MIN(X,Y) ((X) < (Y) ? (X) : (Y))
#define MAX(X,Y) ((X) > (Y) ? (X) : (Y))

//---------------------------------------
// Unions
//---------------------------------------
typedef union pair64_u
{
  uint64_t u64;
  uint32_t u32[2];
  int32_t s32[2];
} pair64_u;

//---------------------------------------
// Function declarations
//---------------------------------------
address_t copy_int16_lut(address_t start_address, uint32_t num_entries, int16_t *lut);

//---------------------------------------
// Plasticity maths function inline implementation
//---------------------------------------
static inline pair64_u pair_int32(int32_t first, int32_t second)
{
  pair64_u pair;
  pair.s32[0] = first;
  pair.s32[1] = second;
  return pair;
}
//---------------------------------------
static inline pair64_u pair_uint32(uint32_t first, uint32_t second)
{
  pair64_u pair;
  pair.u32[0] = first;
  pair.u32[1] = second;
  return pair;
}
//---------------------------------------
static inline uint32_t first_uint32(pair64_u pair)
{
  return pair.u32[0];
}
//---------------------------------------
static inline uint32_t second_uint32(pair64_u pair)
{
  return pair.u32[1];
}
//---------------------------------------
static inline int32_t first_int32(pair64_u pair)
{
  return pair.s32[0];
}
//---------------------------------------
static inline int32_t second_int32(pair64_u pair)
{
  return pair.s32[1];
}
//---------------------------------------
// **NOTE** this should 'encourage' GCC to insert SMULBB/SMULTB 16x16 multiplies
static inline int32_t plasticity_mul_16x16(int16_t x, int16_t y) 
{
  return x * y;
}
//---------------------------------------
static inline uint32_t plasticity_clamp_pot(uint32_t value, uint32_t size)
{
  // Get max and mask from size
  const uint32_t max = size - 1;
  const uint32_t mask = ~max;
  
  return ((value & mask) != 0) ? max : value;
}
//---------------------------------------
static inline int32_t plasticity_exponential_decay(uint32_t time, 
  const uint32_t time_shift, const uint32_t lut_size, const int16_t *lut)
{
  // Calculate lut index
  uint32_t lut_index = time >> time_shift;
  
  // Clamp lut index to (0, lutSize)
  lut_index = plasticity_clamp_pot(lut_index, lut_size);
  
  // Return value from LUT
  return lut[lut_index];
}
//---------------------------------------
static inline int32_t plasticity_fixed_mul16(int32_t a, int32_t b, const int32_t fixed_point_position)
{
  // Extend a and b to 32 bits and multiply - SHOULD compile to SMULBB instruction
  int32_t mul = plasticity_mul_16x16((int16_t)a, (int16_t)b);
  
  // Shift down
  return (mul >> fixed_point_position);
}
//---------------------------------------
static inline int32_t plasticity_fixed_mul32(int32_t a, int32_t b, const int32_t fixed_point_position)
{
  int32_t mul = a * b;
  
  // Shift down and return
  return (mul >> fixed_point_position);
}
//---------------------------------------
static inline uint32_t plasticity_fixed_umul32(uint32_t a, uint32_t b, const uint32_t fixed_point_position)
{
  uint32_t mul = a * b;
  
  // Shift down and return
  return (mul >> fixed_point_position);
}

#endif // MATHS_H