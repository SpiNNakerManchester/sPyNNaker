#include "../../../spin-neuron-impl.h"
#include "additive_one_term_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t plasticity_weight_region_data;

//---------------------------------------
// Functions
//---------------------------------------
address_t plasticity_region_weight_filled (address_t address, uint32_t flags)
{
  use(flags);

  log_info("plasticity_region_weight_filled: starting");
  log_info("\tSTDP additive one-term weight dependance");
  
  // Copy plasticity region data from address
  // **NOTE** this seems somewhat safer than relying on sizeof
  plasticity_weight_region_data.min_weight = (int32_t)address[0];
  plasticity_weight_region_data.max_weight = (int32_t)address[1];
  plasticity_weight_region_data.a2_plus = (int32_t)address[2];
  plasticity_weight_region_data.a2_minus = (int32_t)address[3];
  
  log_info("\tMin weight:%d, Max weight:%d, A2+:%d, A2-:%d", plasticity_weight_region_data.min_weight, plasticity_weight_region_data.max_weight, 
    plasticity_weight_region_data.a2_plus, plasticity_weight_region_data.a2_minus);

  log_info("plasticity_region_weight_filled: completed successfully");

  // Return end address of region
  return &address[4];
}
