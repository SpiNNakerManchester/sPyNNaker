#ifndef EVENTS_IMPL_H
#define EVENTS_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../common/common-impl.h"

//---------------------------------------
// Macros
//---------------------------------------
// Size of post-synaptic event circular queue
#define MAX_POST_SYNAPTIC_EVENTS_BITS 5
#define MAX_POST_SYNAPTIC_EVENTS (1 << MAX_POST_SYNAPTIC_EVENTS_BITS)
#define MAX_POST_SYNAPTIC_EVENTS_MASK (MAX_POST_SYNAPTIC_EVENTS - 1)

// Size of pre-synaptic event buffer
#define MAX_PRE_SYNAPTIC_EVENTS_BITS 2
#define MAX_PRE_SYNAPTIC_EVENTS (1 << MAX_PRE_SYNAPTIC_EVENTS_BITS)
#define MAX_PRE_SYNAPTIC_EVENTS_MASK (MAX_PRE_SYNAPTIC_EVENTS - 1)

//---------------------------------------
// Structures
//---------------------------------------
// Fixed-sized structure located at the start of each synaptic  
// row and containing deferred pre-synaptic events
typedef struct pre_synaptic_event_history_t
{
  uint8_t start_index;
  uint8_t count;
  
  uint32_t times[MAX_PRE_SYNAPTIC_EVENTS];
  pre_synaptic_trace_entry_t traces[MAX_PRE_SYNAPTIC_EVENTS];
} pre_synaptic_event_history_t;

// Wrapper structures combining time with event times for passing around internally
typedef struct post_synaptic_event_t
{
  uint32_t time;
  post_synaptic_trace_entry_t trace;
} post_synaptic_event_t;

typedef struct pre_synaptic_event_t
{
  uint32_t time;
  pre_synaptic_trace_entry_t trace;
} pre_synaptic_event_t;

//---------------------------------------
// Externals
//---------------------------------------
// Post-synaptic event traces
// **NOTE** vectorish format so 8-bit counters and potentially sub 32-bit trace entries can be packed efficiently
extern uint8_t *post_synaptic_event_history_start_index;
extern uint8_t *post_synaptic_event_history_count;
extern uint32_t **post_synaptic_event_history_times;
extern post_synaptic_trace_entry_t **post_synaptic_event_history_traces;

//---------------------------------------
// Function declarations
//---------------------------------------
void initialise_post_synaptic_event_buffers();

//---------------------------------------
// Post-synaptic event history inline implementation
//---------------------------------------
static inline uint32_t post_synaptic_event_next_index(uint32_t event)
{
  return ((event + 1) & MAX_POST_SYNAPTIC_EVENTS_MASK);
}
//---------------------------------------
static inline uint32_t post_synaptic_event_back_index(uint32_t start_index, uint32_t count)
{
  return (start_index + count - 1) & MAX_POST_SYNAPTIC_EVENTS_MASK;
}
//---------------------------------------
static inline uint32_t post_synaptic_event_end_index(uint32_t start_index, uint32_t count)
{
  return (start_index + count) & MAX_POST_SYNAPTIC_EVENTS_MASK;
}
//---------------------------------------
static inline post_synaptic_event_t post_synaptic_event_build(uint32_t time, post_synaptic_trace_entry_t trace)
{
  return (post_synaptic_event_t){ .time = time, .trace = trace };
}
//---------------------------------------
static inline post_synaptic_event_t post_synaptic_event_last(uint32_t neuron)
{
  // If this neuron has no events, return false
  const uint32_t count = post_synaptic_event_history_count[neuron];
  if(count == 0)
  {
    return post_synaptic_event_build(0, trace_rule_get_initial_post_synaptic_trace());
  }
  // Otherwise
  else
  {
    // Calculate back index
    const uint32_t back_index = post_synaptic_event_back_index(post_synaptic_event_history_start_index[neuron], count);

    // Build new post-synaptic event from time and trace
    return post_synaptic_event_build(post_synaptic_event_history_times[neuron][back_index], 
      post_synaptic_event_history_traces[neuron][back_index]);
  }
}
//---------------------------------------
static inline void post_synaptic_event_find_next(uint32_t neuron, uint32_t current_event_index, 
                                                 uint32_t *next_event_index, uint32_t *next_event_time)
{
  // If the current event isn't the last one
  const uint32_t start_index = post_synaptic_event_history_start_index[neuron];
  const uint32_t count = post_synaptic_event_history_count[neuron];
  if(current_event_index != post_synaptic_event_back_index(start_index, count))
  {
    const uint32_t potential_next_event_index = post_synaptic_event_next_index(current_event_index);
    const uint32_t potential_next_event_time = post_synaptic_event_history_times[neuron][potential_next_event_index];
    // **NOTE** no dendritic delays so uneccessary
    //if(potential_next_event_time <= time)
    //{
      // Return index and time of next event
      *next_event_index = potential_next_event_index;
      *next_event_time = potential_next_event_time;
      return;
    //}
  }
  
  // No events remain
  *next_event_time = UINT32_MAX;
  *next_event_index = UINT32_MAX;
}
//---------------------------------------
static inline void post_synaptic_event_find_first(uint32_t neuron, uint32_t last_event_time, 
                                                  uint32_t *next_event_index, uint32_t *next_event_time, 
                                                  post_synaptic_event_t *last_event)
{
  // Initialise last event
  *last_event = post_synaptic_event_build(0, trace_rule_get_initial_post_synaptic_trace());
  
  // Loop through possible events
  const uint32_t start_index = post_synaptic_event_history_start_index[neuron];
  const uint32_t count = post_synaptic_event_history_count[neuron];
  uint32_t e, i;
  for(e = start_index, i = 0; i < count; e = post_synaptic_event_next_index(e), i++)
  {
    // If the next pre-synaptic event's in the past, it's a possible last event but not a next event - continue
    const uint32_t event_time = post_synaptic_event_history_times[neuron][e];
    if(event_time <= last_event_time)
    {
      *last_event = post_synaptic_event_build(event_time, post_synaptic_event_history_traces[neuron][e]);
      continue;
    }
    // If event's in the future stop searching
    // **NOTE** in the absence of dendritic delays this isn't necessary
    /*else if(post_synaptic_event_history[e].time > time)
    {
      break;
    }*/
    // Otherwise, we've found next event
    else
    {
      *next_event_time = event_time;
      *next_event_index = e;
      return;
    }
  }
  
  // No events - There is no subsequent event in the window
  *next_event_index = UINT32_MAX;
  *next_event_time = UINT32_MAX;
}
//---------------------------------------
static inline void post_synaptic_event_add(uint32_t neuron, uint32_t event_time, post_synaptic_trace_entry_t event_trace_entry)
{
  // Add trace and time to end
  const uint32_t current_start_index = post_synaptic_event_history_start_index[neuron];
  const uint32_t current_count = post_synaptic_event_history_count[neuron];
  const uint32_t new_entry_index = post_synaptic_event_end_index(current_start_index, current_count);
  post_synaptic_event_history_times[neuron][new_entry_index] = event_time;
  post_synaptic_event_history_traces[neuron][new_entry_index] = event_trace_entry;
  
  plastic_runtime_log_info("\tInserting post-synaptic event at location %u in queue\n", new_entry_index);

  // If maximum count hasn't been reached, increase count
  if(current_count < MAX_POST_SYNAPTIC_EVENTS)
  {
    post_synaptic_event_history_count[neuron] = current_count + 1;
  }
  // Otherwise, we're eating our own tail so move start forwards
  else
  {
    post_synaptic_event_history_start_index[neuron] = post_synaptic_event_next_index(current_start_index);
  }
  
  plastic_runtime_log_info("\tNew start location:%u, new count:%u\n", post_synaptic_event_history_start_index[neuron], post_synaptic_event_history_count[neuron]);
}

//---------------------------------------
// Pre-synaptic event history inline implementation
//---------------------------------------
static inline uint32_t pre_synaptic_event_next_index(uint32_t event)
{
  return ((event + 1) & MAX_PRE_SYNAPTIC_EVENTS_MASK);
}
//---------------------------------------
static inline uint32_t pre_synaptic_event_back_index(uint32_t start_index, uint32_t count)
{
  return (start_index + count - 1) & MAX_PRE_SYNAPTIC_EVENTS_MASK;
}
//---------------------------------------
static inline uint32_t pre_synaptic_event_end_index(uint32_t start_index, uint32_t count)
{
  return (start_index + count) & MAX_PRE_SYNAPTIC_EVENTS_MASK;
}
//---------------------------------------
static inline pre_synaptic_event_t pre_synaptic_event_build(uint32_t time, pre_synaptic_trace_entry_t trace)
{
  return (pre_synaptic_event_t){ .time = time, .trace = trace };
}
//---------------------------------------
static inline pre_synaptic_event_t pre_synaptic_event_last(const pre_synaptic_event_history_t *event_history)
{
  // If this neuron has no events, return false
  if(event_history->count == 0)
  {
    return pre_synaptic_event_build(0, trace_rule_get_initial_pre_synaptic_trace());
  }
  // Otherwise
  else
  {
    // Calculate back index
    const uint32_t back_index = pre_synaptic_event_back_index(event_history->start_index, event_history->count);

    // Build new pre-synaptic event from time and trace
    return pre_synaptic_event_build(event_history->times[back_index], event_history->traces[back_index]);
  }
}
//---------------------------------------
static inline void pre_synaptic_event_find_next(const pre_synaptic_event_history_t *event_history, uint32_t delay, uint32_t current_event_index, 
                                                 uint32_t *next_event_index, uint32_t *next_event_time)
{
  // If the current event isn't the last one
  if(current_event_index != pre_synaptic_event_back_index(event_history->start_index, event_history->count))
  {
    const uint32_t potential_next_event_index = pre_synaptic_event_next_index(current_event_index);
    const uint32_t potential_next_delayed_event_time = event_history->times[potential_next_event_index] + delay;
    
    // If this event isn't in the future
    if(potential_next_delayed_event_time <= time)
    {
      // Return index and time of next event
      *next_event_index = potential_next_event_index;
      *next_event_time = potential_next_delayed_event_time;
      return;
    }

  }
  
  // No events remain
  *next_event_time = UINT32_MAX;
  *next_event_index = UINT32_MAX;
}
//---------------------------------------
static inline void pre_synaptic_event_find_first(const pre_synaptic_event_history_t *event_history, uint32_t last_event_time, uint32_t delay, 
                                                  uint32_t *next_event_index, uint32_t *next_event_time, 
                                                  pre_synaptic_event_t *last_event)
{
  // Initialise last event
  *last_event = pre_synaptic_event_build(0, trace_rule_get_initial_pre_synaptic_trace());
  
  // Loop through possible events
  uint32_t e, i;
  for(e = event_history->start_index, i = 0; i < event_history->count; e = pre_synaptic_event_next_index(e), i++)
  {
    // If the next pre-synaptic event's in the past, it's a possible last event but not a next event - continue
    const uint32_t delayed_event_time = event_history->times[e] + delay;
    if(delayed_event_time <= last_event_time)
    {
      *last_event = pre_synaptic_event_build(delayed_event_time, event_history->traces[e]);
      continue;
    }
    // If event's in the future stop searching
    else if(delayed_event_time > time)
    {
      break;
    }
    // Otherwise, we've found next event
    else
    {
      *next_event_time = delayed_event_time;
      *next_event_index = e;
      return;
    }
  }
  
  // No events - There is no subsequent event in the window
  *next_event_index = UINT32_MAX;
  *next_event_time = UINT32_MAX;
}
//---------------------------------------
static inline void pre_synaptic_event_add(pre_synaptic_event_history_t *event_history, uint32_t event_time, pre_synaptic_trace_entry_t event_trace_entry)
{
  // Add trace and time to end
  const uint32_t current_start_index = event_history->start_index;
  const uint32_t current_count = event_history->count;
  const uint32_t new_entry_index = pre_synaptic_event_end_index(current_start_index, current_count);
  event_history->times[new_entry_index] = event_time;
  event_history->traces[new_entry_index] = event_trace_entry;
  
  plastic_runtime_log_info("\tInserting pre-synaptic event at location %u in queue\n", new_entry_index);
  
  // If maximum count hasn't been reached, increase count
  if(current_count < MAX_PRE_SYNAPTIC_EVENTS)
  {
    event_history->count = current_count + 1;
  }
  // Otherwise, we're eating our own tail so move start forwards
  else
  {
    event_history->start_index = pre_synaptic_event_next_index(current_start_index);
  }
  
  plastic_runtime_log_info("\tNew start index:%u, new count:%u\n", event_history->start_index, event_history->count);
}

#endif  // EVENTS_IMPL_H