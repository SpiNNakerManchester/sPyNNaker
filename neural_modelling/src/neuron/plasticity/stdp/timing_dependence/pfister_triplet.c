#include "../../../spin-neuron-impl.h"
#include "pfister_triplet_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_plus_lookup[TAU_PLUS_SIZE];
int16_t tau_minus_lookup[TAU_MINUS_SIZE];
int16_t tau_x_lookup[TAU_X_SIZE];
int16_t tau_y_lookup[TAU_Y_SIZE];

// Global plasticity parameter data
plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *plasticity_region_trace_filled(uint32_t* address, uint32_t flags)
{
  use(flags);

  log_info("plasticity_region_trace_filled: starting");
  log_info("\tSTDP triplet rule");
  // **TODO** assert number of neurons is less than max

  // Copy plasticity region data from address
  // **NOTE** this seems somewhat safer than relying on sizeof
  plasticity_trace_region_data.a3_plus = (int32_t)address[0];
  plasticity_trace_region_data.a3_minus = (int32_t)address[1];
  
  log_info("\tA3+=%d, A3-=%d", plasticity_trace_region_data.a3_plus, plasticity_trace_region_data.a3_minus);

  // Copy LUTs from following memory
  address_t lut_address = copy_int16_lut(&address[2], TAU_PLUS_SIZE, &tau_plus_lookup[0]);
  lut_address = copy_int16_lut(lut_address, TAU_MINUS_SIZE, &tau_minus_lookup[0]);
  lut_address = copy_int16_lut(lut_address, TAU_X_SIZE, &tau_x_lookup[0]);
  lut_address = copy_int16_lut(lut_address, TAU_Y_SIZE, &tau_y_lookup[0]);

  log_info("plasticity_region_trace_filled: completed successfully");
  
  // Return address at end of last LUT
  return lut_address;
}