#ifndef STDP_WEIGHT_ADDITIVE_IMPL_H
#define STDP_WEIGHT_ADDITIVE_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

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

#endif  // STDP_WEIGHT_ADDITIVE_IMPL_H