#include "../../../spin-neuron-impl.h"
#include "nearest_pair_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_plus_lookup[TAU_PLUS_SIZE];
int16_t tau_minus_lookup[TAU_MINUS_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *plasticity_region_trace_filled(uint32_t* address, uint32_t flags)
{
  use(flags);

  log_info("plasticity_region_trace_filled: starting");
  log_info("\tSTDP nearest-pair rule");
  // **TODO** assert number of neurons is less than max

  // Copy LUTs from following memory
  address_t lut_address = copy_int16_lut(&address[0], TAU_PLUS_SIZE, &tau_plus_lookup[0]);
  lut_address = copy_int16_lut(lut_address, TAU_MINUS_SIZE, &tau_minus_lookup[0]);

  log_info("plasticity_region_trace_filled: completed successfully");

  return lut_address;
}