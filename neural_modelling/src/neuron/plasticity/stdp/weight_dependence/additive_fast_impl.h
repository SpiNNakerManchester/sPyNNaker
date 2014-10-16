#ifndef ADDITIVE_FAST_IMPL_H
#define ADDITIVE_FAST_IMPL_H

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
typedef struct weight_state_t
{
  int32_t initial_weight;
  
  int32_t potentiation;
  int32_t depression;
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

  return (weight_state_t){ .initial_weight = (int32_t)weight, .potentiation = 0, .depression = 0 };
}
//---------------------------------------
static inline weight_state_t weight_apply_depression(weight_state_t state, int32_t depression)
{
  return (weight_state_t){ .initial_weight = state.initial_weight, .depression = (state.depression + depression), .potentiation = state.potentiation }; 
}
//---------------------------------------
static inline weight_state_t weight_apply_potentiation(weight_state_t state, int32_t potentiation)
{
  return (weight_state_t){ .initial_weight = state.initial_weight, .depression = state.depression, .potentiation = (state.potentiation + potentiation) }; 
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state)
{
  // Scale potentiation and depression
  // **NOTE** A2+ and A2- are pre-scaled into weight format
  int32_t scaled_potentiation = STDP_FIXED_MUL_16X16(new_state.potentiation, plasticity_weight_region_data.a2_plus);
  int32_t scaled_depression = STDP_FIXED_MUL_16X16(new_state.depression, plasticity_weight_region_data.a2_minus);

  // Apply scaled potentiation and depression
  int32_t new_weight = new_state.initial_weight + scaled_potentiation - scaled_depression;

  // Clamp new weight
  new_weight = MIN(plasticity_weight_region_data.max_weight, MAX(new_weight, plasticity_weight_region_data.min_weight));
  
  plastic_runtime_log_info("\told_weight:%u, potentiation:%d, scaled_potentiation:%d, depression:%d, scaled_depression:%d, new_weight:%d\n", 
    new_state.initial_weight, new_state.potentiation, scaled_potentiation, new_state.depression, scaled_depression, new_weight);
  
  return (weight_t)new_weight;
}
#endif  // STDP_WEIGHT_ADDITIVE_FAST_IMPL_H