#ifndef STDP_TYPEDEFS_H
#define STDP_TYPEDEFS_H

//---------------------------------------
// Macros
//---------------------------------------
// Fixed-point number system used STDP
#define STDP_FIXED_POINT 11
#define STDP_FIXED_POINT_ONE (1 << STDP_FIXED_POINT)

// Helper macros for 16-bit fixed-point multiplication
#define STDP_FIXED_MUL_16X16(a, b) plasticity_fixed_mul16(a, b, STDP_FIXED_POINT)

#endif  // STDP_TYPEDEFS_H