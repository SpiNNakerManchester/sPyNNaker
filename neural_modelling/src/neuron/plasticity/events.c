#include "../spin-neuron-impl.h"
#include "events_impl.h"

// **NOTE** trace rule header is included by make file

//---------------------------------------
// Globals
//---------------------------------------
// Post-synaptic event traces
// **NOTE** vectorish format so 8-bit counters and potentially sub 32-bit trace entries can be packed efficiently
uint8_t *post_synaptic_event_history_start_index = NULL;
uint8_t *post_synaptic_event_history_count = NULL;
uint32_t **post_synaptic_event_history_times = NULL;
post_synaptic_trace_entry_t **post_synaptic_event_history_traces = NULL;

//---------------------------------------
// Functions
//---------------------------------------
void initialise_post_synaptic_event_buffers()
{
  log_info("\tPre-synaptic trace structure size:%u, Post-synaptic trace structure size:%u, Pre-synaptic event buffer size:%u", sizeof(post_synaptic_trace_entry_t), sizeof(pre_synaptic_trace_entry_t), sizeof(pre_synaptic_event_history_t));

  // Allocate global STDP structures
  post_synaptic_event_history_start_index = (uint8_t*)spin1_malloc(num_neurons * sizeof(uint8_t));
  post_synaptic_event_history_count = (uint8_t*)spin1_malloc(num_neurons * sizeof(uint8_t));
  
  post_synaptic_event_history_times = (uint32_t**)spin1_malloc(num_neurons * sizeof(uint32_t*));
  post_synaptic_event_history_traces = (post_synaptic_trace_entry_t**)spin1_malloc(num_neurons * sizeof(post_synaptic_trace_entry_t*));
  
  // Check allocations succeeded
  if(post_synaptic_event_history_start_index == NULL || post_synaptic_event_history_count == NULL || post_synaptic_event_history_times == NULL || post_synaptic_event_history_traces == NULL)
  {
    sentinel("Unable to allocate global STDP structures - Out of DTCM");
  }
  
  // Loop through neurons
  for(uint32_t n = 0; n < num_neurons; n++)
  {
    // Zero circular queue control structures
    post_synaptic_event_history_start_index[n] = 0;
    post_synaptic_event_history_count[n] = 0;
    
    // Allocate per-neuron post-synaptic event times
    post_synaptic_event_history_times[n] = (uint32_t*)spin1_malloc(MAX_POST_SYNAPTIC_EVENTS * sizeof(uint32_t));
    if(post_synaptic_event_history_times[n] == NULL)
    {
      sentinel("Unable to allocate post-synaptic event times for neuron %u - Out of DTCM", n);
    }

    // If the post-synaptic event structure isn't empty
    if(sizeof(post_synaptic_trace_entry_t) > 0)
    {
      // Allocate per-neuron post-synaptic event traces
      post_synaptic_event_history_traces[n] = (post_synaptic_trace_entry_t*)spin1_malloc(MAX_POST_SYNAPTIC_EVENTS * sizeof(post_synaptic_trace_entry_t));
      
      // Check allocations succeeded
      if(post_synaptic_event_history_traces[n] == NULL)
      {
        sentinel("Unable to allocate post-synaptic event traces for neuron %u - Out of DTCM", n);
      }
    }
  }
}

