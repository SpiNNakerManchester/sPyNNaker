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
typedef struct
{
  int32_t min_weight;
  int32_t max_weight;
  
  int32_t a2_plus;
  int32_t a2_minus;
} plasticity_weight_region_data_t;

typedef struct
{
  int32_t weight;
  
  uint32_t weight_multiply_right_shift;
  const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];
extern uint32_t weight_multiply_right_shift[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Weight dependance functions
//---------------------------------------
static inline weight_state_t weight_init(weight_t weight, index_t synapse_type)
{
  return (weight_state_t){ 
    .weight = (int32_t)weight, 
    .weight_multiply_right_shift = weight_multiply_right_shift[synapse_type], 
    .weight_region = plasticity_weight_region_data[synapse_type] };
}
//---------------------------------------
static inline weight_state_t weight_apply_depression(weight_state_t state, int32_t depression)
{
  // Calculate scale
  // **NOTE** this calculation must be done at runtime-defined weight fixed-point format
  int32_t scale = plasticity_fixed_mul16(state.weight - state.weight_region->min_weight, 
    state.weight_region->a2_minus, state.weight_multiply_right_shift); 
  
  // Multiply scale by depression and subtract
  // **NOTE** using standard STDP fixed-point format handles format conversion
  return state.weight - STDP_FIXED_MUL_16X16(scale, depression);
}
//---------------------------------------
static inline weight_state_t weight_apply_potentiation(weight_state_t state, int32_t potentiation)
{
  // Calculate scale
  // **NOTE** this calculation must be done at runtime-defined weight fixed-point format
  int32_t scale = plasticity_fixed_mul16(state.weight_region->max_weight - state.weight, 
    state.weight_region->a2_plus, state.weight_multiply_right_shift); 
  
  // Multiply scale by potentiation and add
  // **NOTE** using standard STDP fixed-point format handles format conversion
  return state.weight + STDP_FIXED_MUL_16X16(scale, potentiation);
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state)
{
  plastic_runtime_log_info("\tnew_weight:%d\n", new_state.weight);
  
  return (weight_t)new_state.weight;
}

#endif  // MULTIPLICATIVE_IMPL_H