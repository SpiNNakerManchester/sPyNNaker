#ifndef BCPNN_IMPL_H
#define BCPNN_IMPL_H

// Standard includes
#include <stdint.h>

//---------------------------------------
// Structures
//---------------------------------------
typedef struct post_synaptic_trace_entry_t
{
  int16_t primary;
} post_synaptic_trace_entry_t;

typedef struct bcpnn_state_t

typedef struct pre_synaptic_trace_entry_t
{
  int16_t primary;
  int16_t eligibility;
} pre_synaptic_trace_entry_t;

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_region_data_t plasticity_region_data;

//---------------------------------------
// Trace rule event functions
//---------------------------------------
static inline post_synaptic_trace_entry_t trace_rule_get_initial_post_synaptic_trace()
{
  return (post_synaptic_trace_entry_t){ .primary = plasticity_region_data.initial_primary };
}
//---------------------------------------
static inline pre_synaptic_trace_entry_t trace_rule_get_initial_pre_synaptic_trace()
{
  return (pre_synaptic_trace_entry_t){ .primary = plasticity_region_data.initial_primary, .eligibility = plasticity_region_data.initial_eligibility };
}


//---------------------------------------
static inline pre_synaptic_trace_entry_t stdp_trace_rule_add_pre_synaptic_spike(uint32_t spike_time, uint32_t last_event_time, pre_synaptic_trace_entry_t last_event_trace)
{
  
  
  // Return new pre-synaptic event with decayed trace values with energy for new spike added
  // **NOTE** to improve the numeric range of the r2 and o2 traces, they are pre-multiplied by A3- and A3+ respectively
  return (pre_synaptic_trace_entry_t){ .r1 = new_r1_trace };
}
//---------------------------------------
// **TEMP** will be interface to synaptic structure
static inline deferred_update_state_t stdp_trace_rule_get_initial_deferred_update_state(uint32_t weight)
{
  use(weight);

  return (deferred_update_state_t){ .potentiation = 0, .depression = 0 };
}
//---------------------------------------
// **TEMP** will be interface to synaptic structure
static inline uint32_t stdp_trace_rule_get_final_weight(deferred_update_state_t new_state, uint32_t old_weight)
{

  return new_weight;
}
//---------------------------------------
static inline deferred_update_state_t stdp_trace_rule_apply_deferred_pre_synaptic_spike(uint32_t event_time, pre_synaptic_trace_entry_t event_trace, 
  uint32_t last_post_synaptic_event_time, post_synaptic_trace_entry_t last_post_synaptic_event_trace, 
  deferred_update_state_t previous_state)
{
  // **TODO** update correlation
  
  return (deferred_update_state_t){ .potentiation = previous_state.potentiation, .depression = depression };
}
//---------------------------------------
static inline deferred_update_state_t stdp_trace_rule_apply_deferred_post_synaptic_spike(uint32_t event_time, post_synaptic_trace_entry_t event_trace, 
  uint32_t last_pre_synaptic_event_time, pre_synaptic_trace_entry_t last_pre_synaptic_event_trace, 
  deferred_update_state_t previous_state)
{
  // **TODO** update correlation

  return (deferred_update_state_t){ .potentiation = potentiation, .depression = previous_state.depression  };
}


#endif  // BCPNN_IMPL_H