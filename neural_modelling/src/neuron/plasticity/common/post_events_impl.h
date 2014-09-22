#ifndef POST_EVENTS_IMPL_H
#define POST_EVENTS_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../../common/common-impl.h"

//---------------------------------------
// Macros
//---------------------------------------
#define MAX_POST_SYNAPTIC_EVENTS 32

//---------------------------------------
// Structures
//---------------------------------------
typedef struct
{
  uint32_t count_minus_one;
  
  uint32_t times[MAX_POST_SYNAPTIC_EVENTS];
  post_trace_t traces[MAX_POST_SYNAPTIC_EVENTS];
} post_event_history_t;

typedef struct
{
  post_trace_t prev_trace;
  uint32_t prev_time;
  const post_trace_t *next_trace;
  const uint32_t *next_time;
  uint32_t num_events;
} post_event_window_t;

//---------------------------------------
// Externals
//---------------------------------------
extern post_event_history_t *post_event_history;

//---------------------------------------
// Function declarations
//---------------------------------------
void post_init_buffers();

//---------------------------------------
// Inline functions
//---------------------------------------
static inline post_event_window_t post_get_window(const post_event_history_t *events, uint32_t begin_time)
{
  // Start at end event - beyond end of post-event history
  const uint32_t count = events->count_minus_one + 1;
  const uint32_t *end_event_time = events->times + count;
  const post_trace_t *end_event_trace = events->traces + count;
  const uint32_t *event_time = end_event_time;
  post_event_window_t window;
  do
  {
    // Cache pointer to this event as potential 
    // Next event and go back one event
    // **NOTE** next_time can be invalid
    window.next_time = event_time--;
  } 
  // Keep looping while event occured after start 
  // Of window and we haven't hit beginning of array
  while(*event_time > begin_time && event_time != events->times);
  
  // Deference event to use as previous
  window.prev_time = *event_time;
  
  // Calculate number of events
  window.num_events = (end_event_time - window.next_time);
  
  // Using num_events, find next and previous traces
  window.next_trace = (end_event_trace - window.num_events);
  window.prev_trace = *(window.next_trace - 1);
  
  // Return window
  return window;
}
//---------------------------------------
static inline post_event_window_t post_next(post_event_window_t window)
{
  // Update previous time and increment next time
  window.prev_time = *window.next_time++;
  window.prev_trace = *window.next_trace++;

  // Decrement remining events
  window.num_events--;
  return window;
}
//---------------------------------------
static inline void post_add(post_event_history_t *events, post_trace_t trace)
{
  // If there's still space, store time at current end and increment count minus 1
  if(events->count_minus_one < (MAX_POST_SYNAPTIC_EVENTS - 1))
  {
    const uint32_t new_index = ++events->count_minus_one;
    events->times[new_index] = time;
    events->traces[new_index] = trace;
  }
  // Otherwise
  else
  {
    // Shuffle down elements
    // **NOTE** 1st element is always an entry at time 0
    for(uint32_t e = 2; e < MAX_POST_SYNAPTIC_EVENTS; e++)
    {
      events->times[e - 1] = events->times[e];
      events->traces[e - 1] = events->traces[e];
    }
    
    // Stick new time at end
    events->times[MAX_POST_SYNAPTIC_EVENTS - 1] = time;
    events->traces[MAX_POST_SYNAPTIC_EVENTS - 1] = trace;
  }
}

#endif  // POST_EVENTS_IMPL_H