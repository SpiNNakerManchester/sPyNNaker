#include "../spin-neuron-impl.h"
#include <static-assert.h>
#include "stdp_trace_pair_impl.h"

#include <string.h>

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t stdp_trace_tau_plus_lookup[STDP_TRACE_TAU_PLUS_SIZE];
int16_t stdp_trace_tau_minus_lookup[STDP_TRACE_TAU_MINUS_SIZE];

// Global plasticity parameter data
plasticity_region_data_t plasticity_region_data;

//---------------------------------------
// Functions
//---------------------------------------
bool plasticity_region_filled (uint32_t* address, uint32_t flags)
{
  use(flags);

  log_info("plasticity_region_filled: starting");
  log_info("\tSTDP pair rule");
  // **TODO** assert number of neurons is less than max

  // Copy plasticity region data from address
  // **NOTE** this seems somewhat safer than relying on sizeof
  plasticity_region_data.min_weight = (int32_t)address[0];
  plasticity_region_data.max_weight = (int32_t)address[1];
  plasticity_region_data.a2_plus = (int32_t)address[2];
  plasticity_region_data.a2_minus = (int32_t)address[3];

  log_info("\tMin weight:%d, Max weight:%d, A2+:%d, A2-:%d", plasticity_region_data.min_weight, plasticity_region_data.max_weight,
    plasticity_region_data.a2_plus, plasticity_region_data.a2_minus);

  // Copy LUTs from following memory
  address_t lut_address = copy_int16_lut(&address[4], STDP_TRACE_TAU_PLUS_SIZE, &stdp_trace_tau_plus_lookup[0]);
  lut_address = copy_int16_lut(lut_address, STDP_TRACE_TAU_MINUS_SIZE, &stdp_trace_tau_minus_lookup[0]);

  log_info("plasticity_region_filled: completed successfully");

  return true;
}
