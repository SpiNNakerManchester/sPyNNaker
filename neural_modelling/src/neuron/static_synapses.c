#include "spin-neuron-impl.h"


void initialise_plasticity_buffers()
{

}
//---------------------------------------
void plasticity_process_post_synaptic_event(uint32_t neuron_index)
{
  use(neuron_index);
}
//---------------------------------------
void process_plastic_synapses (address_t plastic, address_t fixed, ring_entry_t *ring_buffer)
{
  use(plastic);
  use(fixed);
  use(ring_buffer);

  sentinel("There should be no plastic synapses!");
}
//---------------------------------------
bool plasticity_region_filled (uint32_t* address, uint32_t flags)
{
  use(address);
  use(flags);
}
//---------------------------------------
void print_plastic_synapses(address_t plastic, address_t fixed)
{
  use(plastic);
  use(fixed);
}
//---------------------------------------
accum plasticity_get_intrinsic_bias(uint32_t j)
{
  use(j);
  
  return 0.0k;
}