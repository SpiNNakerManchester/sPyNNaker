#ifndef _STDP_TYPEDEFS_H_
#define _STDP_TYPEDEFS_H_

//---------------------------------------
// Macros
//---------------------------------------
// Fixed-point number system used STDP
#define STDP_FIXED_POINT 11
#define STDP_FIXED_POINT_ONE (1 << STDP_FIXED_POINT)

// Helper macros for 16-bit fixed-point multiplication
#define STDP_FIXED_MUL_16X16(a, b) maths_fixed_mul16(a, b, STDP_FIXED_POINT)

#define print_plasticity false

#endif  // _STDP_TYPEDEFS_H_
