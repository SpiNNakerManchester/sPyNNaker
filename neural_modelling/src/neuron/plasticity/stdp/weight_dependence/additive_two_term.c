#include "../../../spin-neuron-impl.h"
#include "additive_two_term_impl.h"

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
  log_info("\tSTDP additive two-term  weight dependance");
  
  // Copy plasticity region data from address
  // **NOTE** this seems somewhat safer than relying on sizeof
<<<<<<< HEAD
  int32_t *plasticity_word = (int32_t*)address;
  for(uint32_t s = 0; s < SYNAPSE_TYPE_COUNT; s++)
  {
    plasticity_weight_region_data[s].min_weight = *plasticity_word++;
    plasticity_weight_region_data[s].max_weight = *plasticity_word++;
    plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
    plasticity_weight_region_data[s].a2_minus = *plasticity_word++;
    plasticity_weight_region_data[s].a3_plus = *plasticity_word++;
    plasticity_weight_region_data[s].a3_minus = *plasticity_word++;
    
    log_info("\tSynapse type %u: Min weight:%d, Max weight:%d, A2+:%d, A2-:%d, A3+:%d, A3-:%d", 
      s, plasticity_weight_region_data[s].min_weight, plasticity_weight_region_data[s].max_weight, 
      plasticity_weight_region_data[s].a2_plus, plasticity_weight_region_data[s].a2_minus, 
      plasticity_weight_region_data[s].a3_plus, plasticity_weight_region_data[s].a3_minus);
  }
=======
  plasticity_weight_region_data.min_weight = (int32_t)address[0];
  plasticity_weight_region_data.max_weight = (int32_t)address[1];
  plasticity_weight_region_data.a2_plus = (int32_t)address[2];
  plasticity_weight_region_data.a2_minus = (int32_t)address[3];
  plasticity_weight_region_data.a3_plus = (int32_t)address[4];
  plasticity_weight_region_data.a3_minus = (int32_t)address[5];
  
  log_info("\tMin weight:%d, Max weight:%d, A2+:%d, A2-:%d, A3+%d, A3-:%d", plasticity_weight_region_data.min_weight, plasticity_weight_region_data.max_weight, 
    plasticity_weight_region_data.a2_plus, plasticity_weight_region_data.a2_minus, plasticity_weight_region_data.a3_plus, plasticity_weight_region_data.a3_minus);

>>>>>>> parent of 6909557... Merge remote-tracking branch 'origin/merge_edges_pre_merge' into merge_edges
  log_info("plasticity_region_weight_filled: completed successfully");

  // Return end address of region
  return &address[6];
}
