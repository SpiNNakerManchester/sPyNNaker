#ifndef ADDITIVE_PRESCALED_IMPL_H
#define ADDITIVE_PRESCALED_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../../../common/common-impl.h"

// Include generic plasticity maths functions
#include "../../common/maths.h"
#include "../../common/runtime_log.h"

// Generic additive structures
#include "additive_typedefs.h"

//---------------------------------------
// Structures
//---------------------------------------
typedef int32_t weight_state_t;

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t plasticity_weight_region_data;

//---------------------------------------
// STDP weight dependance functions
//---------------------------------------
static inline weight_state_t weight_init(weight_t weight)
{
  return (int32_t)weight;
}
//---------------------------------------
static inline weight_state_t weight_apply_depression(weight_state_t state, int32_t depression)
{
  return state - depression; 
}
//---------------------------------------
static inline weight_state_t weight_apply_potentiation(weight_state_t state, int32_t potentiation)
{
  return state + potentiation;
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state)
{
  // Clamp weight to hard limits
  int32_t new_weight = MIN(plasticity_weight_region_data.max_weight, MAX(new_state, plasticity_weight_region_data.min_weight));
  
  plastic_runtime_log_info("\tnew_weight:%d\n", new_weight);
  
  return (weight_t)new_weight;
}

#endif  // ADDITIVE_PRESCALED_IMPL_H