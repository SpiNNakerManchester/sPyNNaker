#ifndef STDP_TRACE_PAIR_IMPL
#define STDP_TRACE_PAIR_IMPL

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../common/common-impl.h"

// Include generic plasticity maths functions
#include "maths.h"
#include "runtime_log.h"

//---------------------------------------
// Macros
//---------------------------------------
// Fixed-point number system used for trace-based STDP
#define STDP_TRACE_FIXED_POINT 11
#define STDP_TRACE_FIXED_POINT_ONE (1 << STDP_TRACE_FIXED_POINT)

// When converting result in STDP_TRACE_FIXED_POINT fixed-point format to weight, amount to shift by
#define STDP_TRACE_TO_INPUT_SHIFT_LEFT (15 - STDP_TRACE_FIXED_POINT)

// Exponential decay lookup parameters
#define STDP_TRACE_TAU_PLUS_TIME_SHIFT 0
#define STDP_TRACE_TAU_PLUS_SIZE 256

#define STDP_TRACE_TAU_MINUS_TIME_SHIFT 0
#define STDP_TRACE_TAU_MINUS_SIZE 256

// Helper macros for looking up decays
#define STDP_TRACE_DECAY_LOOKUP_TAU_PLUS(time)  plasticity_exponential_decay(time, STDP_TRACE_TAU_PLUS_TIME_SHIFT, STDP_TRACE_TAU_PLUS_SIZE, stdp_trace_tau_plus_lookup)
#define STDP_TRACE_DECAY_LOOKUP_TAU_MINUS(time)  plasticity_exponential_decay(time, STDP_TRACE_TAU_MINUS_TIME_SHIFT, STDP_TRACE_TAU_MINUS_SIZE, stdp_trace_tau_minus_lookup)

// Helper macros for multiplication
#define STDP_TRACE_FIXED_MUL_16X16(a, b) plasticity_fixed_mul16(a, b, STDP_TRACE_FIXED_POINT)

//---------------------------------------
// Structures
//---------------------------------------
typedef struct post_synaptic_trace_entry_t
{
  int16_t o1;
} post_synaptic_trace_entry_t;

typedef struct pre_synaptic_trace_entry_t
{
  int16_t r1;
} pre_synaptic_trace_entry_t;

typedef struct deferred_update_state_t
{
  int32_t potentiation;
  int32_t depression;
} deferred_update_state_t;

typedef struct
{
  int32_t min_weight;
  int32_t max_weight;

  int32_t a2_plus;
  int32_t a2_minus;
} plasticity_region_data_t;

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t stdp_trace_tau_plus_lookup[STDP_TRACE_TAU_PLUS_SIZE];
extern int16_t stdp_trace_tau_minus_lookup[STDP_TRACE_TAU_MINUS_SIZE];

extern plasticity_region_data_t plasticity_region_data;

extern uint32_t ring_buffer_to_input_left_shift;

//---------------------------------------
// Trace rule event functions
//---------------------------------------
static inline post_synaptic_trace_entry_t trace_rule_get_initial_post_synaptic_trace()
{
  return (post_synaptic_trace_entry_t){ .o1 = 0 };
}
//---------------------------------------
static inline pre_synaptic_trace_entry_t trace_rule_get_initial_pre_synaptic_trace()
{
  return (pre_synaptic_trace_entry_t){ .r1 = 0 };
}

//---------------------------------------
// STDP rule trace update functions
//---------------------------------------
static inline post_synaptic_trace_entry_t stdp_trace_rule_add_post_synaptic_spike(uint32_t spike_time, uint32_t last_event_time, post_synaptic_trace_entry_t last_event_trace)
{
  // Get time since last spike
  uint32_t delta_time = spike_time - last_event_time;

  // Decay previous o1 and o2 traces
  int32_t decayed_o1_trace = STDP_TRACE_FIXED_MUL_16X16(last_event_trace.o1, STDP_TRACE_DECAY_LOOKUP_TAU_MINUS(delta_time));

  // Add energy caused by new spike to trace
  // **NOTE** o2 trace is pre-multiplied by a3_plus
  int32_t new_o1_trace = decayed_o1_trace + STDP_TRACE_FIXED_POINT_ONE;

  plastic_runtime_log_info("\tdelta_time=%d, o1=%d\n", delta_time, new_o1_trace);
  
  // Return new pre- synaptic event with decayed trace values with energy for new spike added
  return (post_synaptic_trace_entry_t){ .o1 = new_o1_trace };
}
//---------------------------------------
static inline pre_synaptic_trace_entry_t stdp_trace_rule_add_pre_synaptic_spike(uint32_t spike_time, uint32_t last_event_time, pre_synaptic_trace_entry_t last_event_trace)
{
  // Get time since last spike
  uint32_t delta_time = spike_time - last_event_time;

  // Decay previous r1 and r2 traces
  int32_t decayed_r1_trace = STDP_TRACE_FIXED_MUL_16X16(last_event_trace.r1, STDP_TRACE_DECAY_LOOKUP_TAU_PLUS(delta_time));

  // Add energy caused by new spike to trace
  int32_t new_r1_trace = decayed_r1_trace + STDP_TRACE_FIXED_POINT_ONE;

  plastic_runtime_log_info("\tdelta_time=%u, r1=%d\n", delta_time, new_r1_trace);
  
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
  // Scale potentiation and depression, shifting down into weight format at the same time
  int32_t scaled_potentiation = plasticity_fixed_mul32(new_state.potentiation, plasticity_region_data.a2_plus, STDP_TRACE_FIXED_POINT + (ring_buffer_to_input_left_shift - STDP_TRACE_TO_INPUT_SHIFT_LEFT));
  int32_t scaled_depression = plasticity_fixed_mul32(new_state.depression, plasticity_region_data.a2_minus, STDP_TRACE_FIXED_POINT + (ring_buffer_to_input_left_shift - STDP_TRACE_TO_INPUT_SHIFT_LEFT));

  // Apply scaled potentiation and depression
  int32_t new_weight = (int32_t)old_weight + scaled_potentiation - scaled_depression;

  // Clamp new weight
  new_weight = MIN(plasticity_region_data.max_weight, MAX(new_weight, plasticity_region_data.min_weight));
  
  plastic_runtime_log_info("\told_weight:%u, potentiation:%d, scaled_potentiation:%d, depression:%d, scaled_depression:%d, new_weight:%d\n", 
    old_weight, new_state.potentiation, scaled_potentiation, new_state.depression, scaled_depression, new_weight);
  
  return (uint32_t)new_weight;
}
//---------------------------------------
static inline deferred_update_state_t stdp_trace_rule_apply_deferred_pre_synaptic_spike(uint32_t event_time, pre_synaptic_trace_entry_t event_trace, 
  uint32_t last_post_synaptic_event_time, post_synaptic_trace_entry_t last_post_synaptic_event_trace, 
  deferred_update_state_t previous_state)
{
  use(&event_trace);

  // Get time of event relative to last post-synaptic event
  uint32_t time_since_last_post_event = event_time - last_post_synaptic_event_time;
  int32_t exponential_decay = STDP_TRACE_DECAY_LOOKUP_TAU_MINUS(time_since_last_post_event);
  int32_t decayed_o1_trace = STDP_TRACE_FIXED_MUL_16X16(last_post_synaptic_event_trace.o1, exponential_decay);

  // Add this to current depression value
  int32_t depression = previous_state.depression + decayed_o1_trace;

  plastic_runtime_log_info("\t\t\ttime_since_last_post_event=%u, decayed_o1_trace=%d, depression=%d\n", 
      time_since_last_post_event, decayed_o1_trace, depression);
  
  return (deferred_update_state_t){ .potentiation = previous_state.potentiation, .depression = depression };
}
//---------------------------------------
static inline deferred_update_state_t stdp_trace_rule_apply_deferred_post_synaptic_spike(uint32_t event_time, post_synaptic_trace_entry_t event_trace, 
  uint32_t last_pre_synaptic_event_time, pre_synaptic_trace_entry_t last_pre_synaptic_event_trace, 
  deferred_update_state_t previous_state)
{
  use(&event_trace);

  // Get time of event relative to last pre-synaptic event
  uint32_t time_since_last_pre_event = event_time - last_pre_synaptic_event_time;
  int32_t exponential_decay = STDP_TRACE_DECAY_LOOKUP_TAU_PLUS(time_since_last_pre_event);
  int32_t decayed_r1_trace = STDP_TRACE_FIXED_MUL_16X16(last_pre_synaptic_event_trace.r1, exponential_decay);

   // Add this to current potentiation total
  int32_t potentiation = previous_state.potentiation + decayed_r1_trace;

  plastic_runtime_log_info("\t\t\ttime_since_last_pre_event=%u, decayed_r1_trace=%d, potentiation=%d\n", 
    time_since_last_pre_event, decayed_r1_trace, potentiation);

  return (deferred_update_state_t){ .potentiation = potentiation, .depression = previous_state.depression  };
}

#endif	// STDP_TRACE_PAIR_IMPL
