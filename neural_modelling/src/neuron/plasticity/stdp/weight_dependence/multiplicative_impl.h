#ifndef MULTIPLICATIVE_IMPL_H
#define MULTIPLICATIVE_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../../../common/common-impl.h"

// Include generic plasticity maths functions
#include "../../common/maths.h"
#include "../../common/runtime_log.h"

//---------------------------------------
// Structures
//---------------------------------------
typedef int32_t weight_state_t;

typedef struct
{
  int32_t min_weight;
  int32_t max_weight;
  
  int32_t a2_plus;
  int32_t a2_minus;
} plasticity_weight_region_data_t;


//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t plasticity_weight_region_data;

//---------------------------------------
// Weight dependance functions
//---------------------------------------
static inline weight_state_t weight_init(weight_t weight)
{
  return (int32_t)weight;
}
//---------------------------------------
static inline weight_state_t stdp_weight_apply_depression(weight_state_t state, int32_t depression)
{
  // Calculate scale
  int32_t scale = STDP_TRACE_FIXED_MUL_16X16(state - plasticity_weight_region_data.min_weight, plasticity_weight_region_data.a2_minus); 
  
  // Multiply scale by depression and subtract
  return state - STDP_TRACE_FIXED_MUL_16X16(scale, depression);
}
//---------------------------------------
static inline weight_state_t weight_apply_potentiation(weight_state_t state, int32_t potentiation)
{
  // Calculate scale
  int32_t scale = STDP_TRACE_FIXED_MUL_16X16(plasticity_weight_region_data.max_weight - state, plasticity_weight_region_data.a2_plus); 
  
  // Multiply scale by potentiation and add
  return state + STDP_TRACE_FIXED_MUL_16X16(scale, potentiation);
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state)
{
  plastic_runtime_log_info("\tnew_weight:%d\n", new_state);
  
  return (weight_t)new_state;
}

#endif  // MULTIPLICATIVE_IMPL_H