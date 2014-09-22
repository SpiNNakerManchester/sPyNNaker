#ifndef NEAREST_PAIR_IMPL
#define NEAREST_PAIR_IMPL

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../../spin-neuron-impl.h"

// Include generic plasticity maths functions
#include "../../common/maths.h"
#include "../../common/runtime_log.h"
#include "../../common/synapse_weight_impl.h"

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_PLUS_TIME_SHIFT 0
#define TAU_PLUS_SIZE 256

#define TAU_MINUS_TIME_SHIFT 0
#define TAU_MINUS_SIZE 256

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU_PLUS(time)  plasticity_exponential_decay(time, TAU_PLUS_TIME_SHIFT, TAU_PLUS_SIZE, tau_plus_lookup)
#define DECAY_LOOKUP_TAU_MINUS(time)  plasticity_exponential_decay(time, TAU_MINUS_TIME_SHIFT, TAU_MINUS_SIZE, tau_minus_lookup)

//---------------------------------------
// Structures
//---------------------------------------
typedef struct post_trace_t
{
} post_trace_t;

typedef struct pre_trace_t
{
} pre_trace_t;

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_plus_lookup[TAU_PLUS_SIZE];
extern int16_t tau_minus_lookup[TAU_MINUS_SIZE];

//---------------------------------------
// Declared functions
//---------------------------------------
uint32_t *plasticity_region_trace_filled(uint32_t* address, uint32_t flags);

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace()
{
  return (post_trace_t){};
}
//---------------------------------------
static inline post_trace_t timing_add_post_spike(uint32_t last_time, post_trace_t last_trace)
{
  use(&last_time);
  use(&last_trace);

  plastic_runtime_log_info("\tdelta_time=%u\n", time - last_time);
  
  // Return new pre- synaptic event with decayed trace values with energy for new spike added
  return (post_trace_t){};
}
//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(uint32_t last_time, pre_trace_t last_trace)
{
  use(&last_time);
  use(&last_trace);

  plastic_runtime_log_info("\tdelta_time=%u\n", time - last_time);
  
  return (pre_trace_t){};
}
//---------------------------------------
static inline update_state_t timing_apply_pre_spike(uint32_t time, pre_trace_t trace, 
  uint32_t last_pre_time, pre_trace_t last_pre_trace, 
  uint32_t last_post_time, post_trace_t last_post_trace, 
  update_state_t previous_state)
{
  use(&trace);
  use(&last_pre_time);
  use(&last_pre_trace);
  use(&last_post_trace);

  // Get time of event relative to last post-synaptic event
  uint32_t time_since_last_post = time - last_post_time;
  int32_t decayed_o1 = DECAY_LOOKUP_TAU_MINUS(time_since_last_post);

  plastic_runtime_log_info("\t\t\ttime_since_last_post=%u, decayed_o1=%d\n", 
    time_since_last_post, decayed_o1);
  
  // Apply depression to state (which is a weight_state)
  return weight_apply_depression(previous_state, decayed_o1);
}
//---------------------------------------
static inline update_state_t timing_apply_post_spike(uint32_t time, post_trace_t trace, 
  uint32_t last_pre_time, pre_trace_t last_pre_trace, 
  uint32_t last_post_time, post_trace_t last_post_trace, 
  update_state_t previous_state)
{
  use(&trace);
  use(&last_pre_trace);
  use(&last_post_time);
  use(&last_post_trace);

  // Get time of event relative to last pre-synaptic event
  uint32_t time_since_last_pre = time - last_pre_time;
  int32_t decayed_r1 = DECAY_LOOKUP_TAU_PLUS(time_since_last_pre);

  plastic_runtime_log_info("\t\t\ttime_since_last_pret=%u, decayed_r1=%d\n", 
    time_since_last_pre, decayed_r1);

  // Apply potentiation to state (which is a weight_state)
  return weight_apply_potentiation(previous_state, decayed_r1);
}

#endif	// NEAREST_PAIR_IMPL
