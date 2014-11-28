#ifndef PFISTER_TRIPLET_IMPL_H
#define PFISTER_TRIPLET_IMPL_H

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

#define TAU_X_TIME_SHIFT 2
#define TAU_X_SIZE 256

#define TAU_Y_TIME_SHIFT 2
#define TAU_Y_SIZE 256

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU_PLUS(time)  plasticity_exponential_decay(time, TAU_PLUS_TIME_SHIFT, TAU_PLUS_SIZE, tau_plus_lookup)
#define DECAY_LOOKUP_TAU_MINUS(time)  plasticity_exponential_decay(time, TAU_MINUS_TIME_SHIFT, TAU_MINUS_SIZE, tau_minus_lookup)
#define DECAY_LOOKUP_TAU_X(time)  plasticity_exponential_decay(time, TAU_X_TIME_SHIFT, TAU_X_SIZE, tau_x_lookup)
#define DECAY_LOOKUP_TAU_Y(time)  plasticity_exponential_decay(time, TAU_Y_TIME_SHIFT, TAU_Y_SIZE, tau_y_lookup)

//---------------------------------------
// Structures
//---------------------------------------
typedef struct post_trace_t
{
  int16_t o1;
  int16_t o2;
} post_trace_t;

typedef struct pre_trace_t
{
  int16_t r1;
  int16_t r2;
} pre_trace_t;

typedef struct
{
  int32_t a3_plus;
  int32_t a3_minus;
} plasticity_trace_region_data_t;

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_plus_lookup[TAU_PLUS_SIZE];
extern int16_t tau_minus_lookup[TAU_MINUS_SIZE];
extern int16_t tau_x_lookup[TAU_X_SIZE];
extern int16_t tau_y_lookup[TAU_Y_SIZE];

extern plasticity_trace_region_data_t plasticity_trace_region_data;
extern plasticity_weight_region_data_t plasticity_weight_region_data;

//---------------------------------------
// Declared functions
//---------------------------------------
uint32_t *plasticity_region_trace_filled(uint32_t* address, uint32_t flags);

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace()
{
  return (post_trace_t){ .o1 = 0, .o2 = 0 };
}
//---------------------------------------
static inline post_trace_t timing_add_post_spike(uint32_t last_time, post_trace_t last_trace)
{
  // Get time since last spike
  uint32_t delta_time = time - last_time;

  // Decay previous o1 trace and add energy caused by new spike
  int32_t decayed_o1 = STDP_FIXED_MUL_16X16(last_trace.o1, DECAY_LOOKUP_TAU_MINUS(delta_time));
  int32_t new_o1 = decayed_o1 + STDP_FIXED_POINT_ONE;
  
  // If this is the 1st post-synaptic event, o2 trace is zero (as it's sampled BEFORE the spike), otherwise, add on energy caused by last spike  and decay that
  int32_t new_o2 = (last_time == 0) ? 0 : STDP_FIXED_MUL_16X16(last_trace.o2 + STDP_FIXED_POINT_ONE, DECAY_LOOKUP_TAU_Y(delta_time));
  
  plastic_runtime_log_info("\tdelta_time=%d, o1=%d, o2=%d\n", delta_time, new_o1, new_o2);
  
  // Return new pre- synaptic event with decayed trace values with energy for new spike added
  return (post_trace_t){ .o1 = new_o1, .o2 = new_o2 };
}
//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(uint32_t last_time, pre_trace_t last_trace)
{
  // Get time since last spike
  uint32_t delta_time = time - last_time;

  // Decay previous r1 trace and add energy caused by new spike
  int32_t decayed_r1 = STDP_FIXED_MUL_16X16(last_trace.r1, DECAY_LOOKUP_TAU_PLUS(delta_time));
  int32_t new_r1 = decayed_r1 + STDP_FIXED_POINT_ONE;
  
  // If this is the 1st pre-synaptic event, r2 trace is zero (as it's sampled BEFORE the spike), otherwise, add on energy caused by last spike  and decay that
  int32_t new_r2 = (last_time == 0) ? 0 : STDP_FIXED_MUL_16X16(last_trace.r2 + STDP_FIXED_POINT_ONE, DECAY_LOOKUP_TAU_X(delta_time));
  
  plastic_runtime_log_info("\tdelta_time=%u, r1=%d, r2=%d\n", delta_time, new_r1, new_r2);
  
  // Return new pre-synaptic event with decayed trace values with energy for new spike added
  return (pre_trace_t){ .r1 = new_r1, .r2 = new_r2 };
}
//---------------------------------------
static inline update_state_t timing_apply_pre_spike(uint32_t time, pre_trace_t trace, 
  uint32_t last_pre_time, pre_trace_t last_pre_trace, 
  uint32_t last_post_time, post_trace_t last_post_trace, 
  update_state_t previous_state)
{
  use(last_pre_time);
  use(&last_pre_trace);
  
  // Get time of event relative to last post-synaptic event
  uint32_t time_since_last_post = time - last_post_time;
  int32_t decayed_o1 = STDP_FIXED_MUL_16X16(last_post_trace.o1, DECAY_LOOKUP_TAU_MINUS(time_since_last_post));
  
  // Calculate depression
  int32_t inner = plasticity_weight_region_data.a2_minus + STDP_FIXED_MUL_16X16(trace.r2, plasticity_trace_region_data.a3_minus);
  int32_t depression = STDP_FIXED_MUL_16X16(decayed_o1, inner);
  
  plastic_runtime_log_info("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d, r2=%d, depression=%d\n", 
                           time_since_last_post, decayed_o1, trace.r2, depression);
  
  // Apply depression to state (which is a weight_state)
  return weight_apply_depression(previous_state, depression);
}
//---------------------------------------
static inline update_state_t timing_apply_post_spike(uint32_t time, post_trace_t trace, 
  uint32_t last_pre_time, pre_trace_t last_pre_trace, 
  uint32_t last_post_time, post_trace_t last_post_trace, 
  update_state_t previous_state)
{
  use(last_post_time);
  use(&last_post_trace);
  
  // Get time of event relative to last pre-synaptic event
  uint32_t time_since_last_pre = time - last_pre_time;
  int32_t decayed_r1 = STDP_FIXED_MUL_16X16(last_pre_trace.r1, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre));

   // Add this to current potentiation total
  int32_t inner = plasticity_weight_region_data.a2_plus + STDP_FIXED_MUL_16X16(trace.o2, plasticity_trace_region_data.a3_plus);
  int32_t potentiation = STDP_FIXED_MUL_16X16(decayed_r1, inner);

  plastic_runtime_log_info("\t\t\ttime_since_last_pre_event=%u, decayed_r1=%d, o2=%d, potentiation=%d\n", 
                           time_since_last_pre, decayed_r1, trace.o2, potentiation);

  // Apply potentiation to state (which is a weight_state)
  return weight_apply_potentiation(previous_state, potentiation);
}

#endif	// PFISTER_TRIPLET_IMPL_H
