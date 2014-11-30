#ifndef ADDITIVE_TWO_TERM_IMPL_H
#define ADDITIVE_TWO_TERM_IMPL_H

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
typedef struct
{
  int32_t min_weight;
  int32_t max_weight;
  
  int32_t a2_plus;
  int32_t a2_minus;
  int32_t a3_plus;
  int32_t a3_minus;
} plasticity_weight_region_data_t;

typedef struct weight_state_t
{
  int32_t initial_weight;
  
  int32_t a2_plus;
  int32_t a2_minus;
  int32_t a3_plus;
  int32_t a3_minus;
} weight_state_t;

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t plasticity_weight_region_data;

//---------------------------------------
// STDP weight dependance functions
//---------------------------------------
static inline weight_state_t weight_init(weight_t weight)
{
  use(weight);

  return (weight_state_t){ .initial_weight = (int32_t)weight, .a2_plus = 0, .a2_minus = 0, .a3_plus = 0, .a3_minus = 0 };
}
//---------------------------------------
static inline weight_state_t weight_apply_depression(weight_state_t state, int32_t a2_minus, int32_t a3_minus)
{
  state.a2_minus += a2_minus;
  state.a3_minus += a3_minus;
  return state;
}
//---------------------------------------
static inline weight_state_t weight_apply_potentiation(weight_state_t state, int32_t a2_plus, int32_t a3_plus)
{
  state.a2_plus += a2_plus;
  state.a3_plus += a3_plus;
  return state;
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state)
{
  // Scale potentiation and depression
  // **NOTE** A2+, A2-, A3+ and A3- are pre-scaled into weight format
  int32_t scaled_a2_plus = STDP_FIXED_MUL_16X16(new_state.a2_plus, plasticity_weight_region_data.a2_plus);
  int32_t scaled_a2_minus = STDP_FIXED_MUL_16X16(new_state.a2_minus, plasticity_weight_region_data.a2_minus);
  int32_t scaled_a3_plus = STDP_FIXED_MUL_16X16(new_state.a3_plus, plasticity_weight_region_data.a3_plus);
  int32_t scaled_a3_minus = STDP_FIXED_MUL_16X16(new_state.a3_minus, plasticity_weight_region_data.a3_minus);
  
  // Apply all terms to initial weight
  int32_t new_weight = new_state.initial_weight + scaled_a2_plus + scaled_a3_plus - scaled_a2_minus - scaled_a3_minus;

  // Clamp new weight
  new_weight = MIN(plasticity_weight_region_data.max_weight, MAX(new_weight, plasticity_weight_region_data.min_weight));
  
  plastic_runtime_log_info("\told_weight:%u, a2+:%d, a2-:%d, a3+:%d, a3-:%d",
    new_state.initial_weight, new_state.a2_plus, new_state.a2_minus, new_state.a3_plus, new_state.a3_minus);
  plastic_runtime_log_info("\tscaled a2+:%d, scaled a2-:%d, scaled a3+:%d, scaled a3-:%d, new_weight:%d",
    scaled_a2_plus, scaled_a2_minus, scaled_a3_plus, scaled_a3_minus, new_weight); 
  
  return (weight_t)new_weight;
}
#endif  // ADDITIVE_TWO_TERM_IMPL_H