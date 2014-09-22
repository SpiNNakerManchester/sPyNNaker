#include "../../spin-neuron-impl.h"
#include "../../synapses_impl.h"
#include "../../../common/compile_time_assert.h"
#include "../common/maths.h"
#include "../common/runtime_log.h"
#include "../common/pre_events_impl.h"
#include "../common/post_events_impl.h"
#include <string.h>

#ifdef DEBUG
bool plastic_runtime_log_enabled = false;
#endif	// DEBUG

//---------------------------------------
// Externals
//---------------------------------------
extern uint32_t num_plastic_pre_synaptic_events;

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline final_state_t plasticity_update_synapse(uint32_t begin_time, uint32_t delay, update_state_t current_state,
  const pre_event_history_t *pre_event_history, const post_event_history_t *post_event_history_t)
{
  // Get the pre-synaptic window of events to be processed
  pre_event_window_t pre_window = pre_get_window(pre_event_history, delay, begin_time);

  // Get the post-synaptic window of events to be processed
  post_event_window_t post_window = post_get_window(post_event_history_t, begin_time);

  plastic_runtime_log_info("\tPerforming deferred synapse update at time:%u - pre_window.prev_time:%u, pre_window.num_events:%u, post_window.prev_time:%u, post_window.num_events:%u\n", 
    time, pre_window.prev_time, pre_window.num_events, post_window.prev_time, post_window.num_events);

  // Process events that occur within window
  while(true)
  {
    // Are the next pre and post-synaptic events valid?
    const bool pre_valid = (pre_window.num_events > 0);
    const bool post_valid = (post_window.num_events > 0);
    
    // If next pre-synaptic event occurs before the next post-synaptic event
    // **NOTE** If next pre-synaptic event time's UINT32_MAX, this will never be true and due to loop conditions, both will never be UINT32_MAX!
    if(pre_valid && (!post_valid || (*pre_window.next_time + delay) <= *post_window.next_time))
    {
      plastic_runtime_log_info("\t\tApplying pre-synaptic event at time:%u\n", *pre_window.next_time + delay);
      
      // Apply spike to state
      const uint32_t delayed_pre_time = *pre_window.next_time + delay;
      current_state = timing_apply_pre_spike(delayed_pre_time, *pre_window.next_trace, 
        pre_window.prev_time, pre_window.prev_trace, 
        post_window.prev_time, post_window.prev_trace, 
        current_state);

      // Go onto next event
      pre_window = pre_next(pre_window, delayed_pre_time);
    }
    // Otherwise, if the next post-synaptic event occurs before the next pre-synaptic event
    else if(post_valid && (!pre_valid || *post_window.next_time <= (*pre_window.next_time + delay)))
    {
      plastic_runtime_log_info("\t\tApplying post-synaptic event at time:%u\n", *post_window.next_time);
      
      // Apply spike to state
      current_state = timing_apply_post_spike(*post_window.next_time, *post_window.next_trace, 
        pre_window.prev_time, pre_window.prev_trace, 
        post_window.prev_time, post_window.prev_trace, 
        current_state);
      
      // Go onto next event
      post_window = post_next(post_window);
    }
    // Otherwise, there's no more events so stop
    else
    {
      break;
    }
  }

  // Return final synaptic word and weight
  return synapse_get_final(current_state);
}

//---------------------------------------
// PACMAN memory region reading
//---------------------------------------
void initialise_plasticity_buffers()
{
  log_info("initialise_plasticity_buffers: starting");
  
  post_init_buffers();
  
  log_info("initialise_plasticity_buffers: completed successfully");
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline plastic_synapse_t* plastic_synapses(address_t plastic)
{
  const uint32_t pre_event_history_size_words = sizeof(pre_event_history_t) / sizeof(uint32_t);
  COMPILE_TIME_ASSERT(pre_event_history_size_words * sizeof(uint32_t) == sizeof(pre_event_history_t), pre_event_history_t_should_be_word_padded)

  return (plastic_synapse_t*)(&plastic[pre_event_history_size_words]); 
}
//---------------------------------------
static inline pre_event_history_t *plastic_event_history(address_t plastic)
{
  return (pre_event_history_t*)(&plastic[0]);
}
//---------------------------------------
void plasticity_process_post_synaptic_event(uint32_t j)
{
#ifdef DEBUG
  plastic_runtime_log_enabled = true;
#endif  // DEBUG

  plastic_runtime_log_info("Processing post-synaptic event at time:%u\n", time);
  
  // Add post-event
  post_event_history_t *history = &post_event_history[j];
  const uint32_t last_post_time = history->times[history->count_minus_one];
  const post_trace_t last_post_trace = history->traces[history->count_minus_one];
  post_add(history, timing_add_post_spike(last_post_time, last_post_trace));
}
//---------------------------------------
void process_plastic_synapses (address_t plastic, address_t fixed, ring_entry_t *ring_buffer)
{
#ifdef DEBUG
  plastic_runtime_log_enabled = true;
#endif  // DEBUG

  // Extract seperate arrays of plastic synapses (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  plastic_synapse_t *plastic_words = plastic_synapses(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);

  // Get event history from synaptic row
  pre_event_history_t *event_history = plastic_event_history(plastic);

  // Get last pre-synaptic event from event history
  // **NOTE** at this level we don't care about individual synaptic delays
  const uint32_t last_pre_time = event_history->times[event_history->count_minus_one];
  num_plastic_pre_synaptic_events += plastic_synapse;
  
  // Loop through plastic synapses
  for ( ; plastic_synapse > 0; plastic_synapse--) 
  {
    // Get next control word (autoincrementing)
    uint32_t control_word = *control_words++;

     // Extract control-word components
    // **NOTE** cunningly, control word is just the same as lower 
    // 16-bits of 32-bit fixed synapse so same functions can be used
    uint32_t delay = sparse_delay(control_word);
    uint32_t index = sparse_type_index(control_word);
    
    // Create update state from the plastic synaptic word
    update_state_t current_state = synapse_init(*plastic_words);
    
    // Update the synapse state
    final_state_t final_state = plasticity_update_synapse(last_pre_time, delay, current_state, event_history, &post_event_history[index]);

    // Convert into ring buffer offset
    uint32_t offset = offset_sparse(delay + time, index);

    // Add weight to ring-buffer entry
    // **NOTE** Dave suspects that this could be a potential location for overflow
    ring_buffer[offset] += final_state.weight;

    // Write back updated synaptic word to plastic region
    *plastic_words++ = final_state.synaptic_word;
  }

  plastic_runtime_log_info("Processing pre-synaptic event at time:%u", time);

  // Add pre-event
  const pre_trace_t last_pre_trace = event_history->traces[event_history->count_minus_one];
  pre_add(event_history, timing_add_pre_spike(last_pre_time, last_pre_trace));
}
//---------------------------------------
bool plasticity_region_filled (uint32_t *address, uint32_t flags)
{
  use(flags);
  
  // Load weight dependence data
  address = plasticity_region_weight_filled(address, flags);
  
  // Load trace rule data
  plasticity_region_trace_filled(address, flags);
  
  return true;
}
//---------------------------------------
#ifdef DEBUG
void print_plastic_synapses(address_t plastic, address_t fixed)
{
  // Extract seperate arrays of weights (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  weight_t *plastic_words = plastic_synapses(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);
  const pre_event_history_t *event_history = plastic_event_history(plastic);

  printf ("Plastic region %u synapses pre-synaptic event buffer count:%u:\n", plastic_synapse, event_history->count_minus_one + 1);

  // Loop through plastic synapses
  for (uint32_t i = 0; i < plastic_synapse; i++) 
  {
    // Get next weight and control word (autoincrementing control word)
    uint32_t weight = *plastic_words++;
    uint32_t control_word = *control_words++;

    printf ("%08x [%3d: (w: %5u (=", control_word, i, weight);
    print_weight (weight);
    printf ("nA) d: %2u, %c, n = %3u)] - {%08x %08x}\n",
      sparse_delay(control_word),
      (sparse_type(control_word)==0)? 'X': 'I',
      sparse_index(control_word),
      SYNAPSE_DELAY_MASK,
      SYNAPSE_TYPE_INDEX_BITS
    );
  }
}
#endif  // DEBUG