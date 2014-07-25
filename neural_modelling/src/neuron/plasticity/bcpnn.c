#include "../spin-neuron-impl.h"
#include "../synapses_impl.h"
#include "../../common/compile_time_assert.h"
#include "bcpnn_impl.h"
#include "events_impl.h"
#include "runtime_log.h"

//---------------------------------------
// Macros
//---------------------------------------
// Fixed-point number system used for trace-based STDP
#define BCPNN_FIXED_POINT 11
#define BCPNN_FIXED_POINT_ONE (1 << STDP_TRACE_FIXED_POINT)

// When converting result in STDP_TRACE_FIXED_POINT fixed-point format to weight, amount to shift by
#define BCPNN_TRACE_TO_WEIGHT_SHIFT_RIGHT (STDP_TRACE_FIXED_POINT - 4)

// Exponential decay lookup parameters
#define BCPNN_PRIMARY_TIME_SHIFT 0
#define BCPNN_PRIMARY_SIZE 256

#define BCPNN_ELIGIBILITY_TIME_SHIFT 2
#define BCPNN_ELIGIBILITY_SIZE 4096

// Fractional log lookup parameters
#define BCPNN_FRACTIONAL_LOG_SIZE 128
#define BCPNN_FRACTIONAL_LOG_INPUT_SHIFT 4

// Helper macros for looking up decays
#define BCPNN_DECAY_LOOKUP_PRIMARY(time)  plasticity_exponential_decay(time, BCPNN_PRIMARY_TIME_SHIFT, BCPNN_PRIMARY_SIZE, bcpnn_primary_lookup)
#define BCPNN_DECAY_LOOKUP_ELIGIBILITY(time)  plasticity_exponential_decay(time, BCPNN_ELIGIBILITY_TIME_SHIFT, BCPNN_ELIGIBILITY_SIZE, bcpnn_eligibility_lookup)

// Helper macros for multiplication
#define BCPNN_FIXED_MUL_16X16(a, b) plasticity_fixed_mul16(a, b, BCPNN_FIXED_POINT)
#define BCPNN_FIXED_MUL_32X32(a, b) plasticity_fixed_mul32(a, b, BCPNN_FIXED_POINT)

//---------------------------------------
// Structures
//---------------------------------------
typedef struct plasticity_region_data_t
{
  int32_t eligibility_primary_reciprocal;
  int32_t two_eligibility_primary_reciprocal;
  int32_t log2_to_natural_log_convert;
  
  int32_t epsilon;
  int32_t epsilon_squared;
  
  int32_t spike_height;
  int32_t initial_primary;
  int32_t initial_eligibility;
  
  int32_t weight_gain;
} plasticity_region_data_t;

// Standardised representation of BCPNN events
typedef struct bcpnn_event_t
{
  uint32_t time;
  int16_t primary_trace;
  int16_t eligibility_trace;
} bcpnn_event_t;

typedef struct deferred_update_state_t
{
  uint32_t time;
  int32_t correlated_eligibility_trace;
} deferred_update_state_t;

//---------------------------------------
// Globals
//---------------------------------------
static int16_t bcpnn_primary_lookup[BCPNN_PRIMARY_SIZE];
static int16_t bcpnn_eligibility_lookup[BCPNN_ELIGIBILITY_SIZE];
static int16_t bcpnn_fractional_log_lookup[BCPNN_FRACTIONAL_LOG_SIZE];

static int16_t *post_synaptic_eligibility = NULL;

plasticity_region_data_t plasticity_region_data;

#ifdef DEBUG
bool plastic_runtime_log_enabled = false;
#endif  // DEBUG

//---------------------------------------
// Maths functions
//---------------------------------------
static inline int32_t bcpnn_fractional_ln(int32_t value)
{ 
  // Use CLZ to get integer log2 of value
  int32_t integer_log2 = 31 - __builtin_clz(value);
  
  // Use this to extract fractional part (should be in range of fixed-point (1.0, 2.0)
  int32_t fractional_part = (value << BCPNN_FIXED_POINT) >> integer_log2;
  
  // Convert this to LUT index and thus get log2 of fractional part
  int fractional_part_lookup_index = (fractional_part - BCPNN_FIXED_POINT_ONE) >> BCPNN_FRACTIONAL_LOG_INPUT_SHIFT;
  int fractional_part_ln = bcpnn_fractional_log_lookup[fractional_part_lookup_index];
  
  // Scale the integer log2 to fixed point and multiply to get integer natural log
  // **TODO** log2 to natural could be a compile time constant
  int integer_part_ln = plasticity_mul_16x16(integer_log2 - BCPNN_FIXED_POINT, plasticity_region_data.log2_to_natural_log_convert);
  
  // Add the two logs together and return
  return fractional_part_ln + integer_part_ln;
}

//---------------------------------------
// BCPNN event queue helper functions
//---------------------------------------
static inline bcpnn_event_t bcpnn_post_synaptic_event_last(uint32_t neuron)
{
  // Get last event from queue
  post_synaptic_event_t last_event = post_synaptic_event_last(neuron);
  
  // Combine this with neuron's last eligibility and return
  return (bcpnn_event_t){ .time = last_event.time, .primary_trace = last_event.trace.primary, .eligibility_trace = post_synaptic_eligibility[neuron] };
}
//---------------------------------------
static inline bcpnn_event_t bcpnn_pre_synaptic_event_last(const pre_synaptic_event_history_t *event_history)
{
  // Get last event from queue and convert into bcpnn event
  pre_synaptic_event_t last_event = pre_synaptic_event_last(event_history);
  return (bcpnn_event_t){ .time = last_event.time, .primary_trace = last_event.trace.primary, .eligibility_trace = last_event.trace.eligibility }
}

//---------------------------------------
// BCPNN trace update functions
//---------------------------------------
static inline int16_t bcpnn_update_primary_trace(uint32_t current_time, uint32_t last_event_time, int16_t last_primary_trace)
{
  // Get time since last event
  uint32_t delta_time = current_time - last_event_time;
  
  // Lookup exponential decay over delta-tim
  int32_t primary_decay = BCPNN_DECAY_LOOKUP_PRIMARY(delta_time);
  int32_t eligibility_decay = BCPNN_DECAY_LOOKUP_ELIGIBILITY(delta_time);
  
  // Multiply by last primary trace value and return
  return BCPNN_FIXED_MUL_16X16(primary_decay, last_primary_trace);
}
//---------------------------------------
static inline int16_t bcpnn_update_eligibility_trace(uint32_t current_time, uint32_t last_event_time, int16_t last_primary_trace, int16_t last_eligibility_trace)
{
  // Get time since last event
  uint32_t delta_time = current_time - last_event_time;
  
  // Lookup exponential decay over delta-tim
  int32_t primary_decay = BCPNN_DECAY_LOOKUP_PRIMARY(delta_time);
  int32_t eligibility_decay = BCPNN_DECAY_LOOKUP_ELIGIBILITY(delta_time);
  
  // Multiply last primary trace value by constant
  // **TODO** is it necessary to use 32-bits here
  int32_t last_spike_eligility_constant = BCPNN_FIXED_MUL_16X16(last_event.primary_trace, plasticity_region_data.eligibility_primary_reciprocal);
  
  // Calculate terms for eligibility trace
  int32_t eligibility_primary_term = BCPNN_FIXED_MUL_16X16(last_spike_eligility_constant, primary_decay);
  int32_t eligibility_decay_term = BCPNN_FIXED_MUL_16X16(last_event.eligibility_trace - last_spike_eligility_constant, eligibility_decay);
  
  int32_t new_eligibility_trace = eligibility_primary_term + eligibility_decay_term;
  
  plastic_runtime_log_info("\t\tbcpnn_add_spike: delta_time:%u, new_eligibility_trace:%d\n", delta_time, new_eligibility_trace);
  
  // Return new eligibility trace value
  return new_eligibility_trace;
}
//---------------------------------------
static inline bcpnn_event_t bcpnn_add_spike(uint32_t spike_time, bcpnn_event_t last_event)
{
  // Get time since last spike
  uint32_t delta_time = spike_time - last_event.time;
  
  // Lookup exponential decay over delta-time with both time constants
  int32_t primary_decay = BCPNN_DECAY_LOOKUP_PRIMARY(delta_time);
  int32_t eligibility_decay = BCPNN_DECAY_LOOKUP_ELIGIBILITY(delta_time);
  
  // Calculate new primary trace value
  int32_t new_primary_trace = BCPNN_FIXED_MUL_16X16(primary_decay, last_event.primary_trace) + plasticity_region_data.spike_height;
  
  // Multiply last primary trace value by constant
  // **TODO** is it necessary to use 32-bits here
  int32_t last_spike_eligility_constant = BCPNN_FIXED_MUL_16X16(last_event.primary_trace, plasticity_region_data.eligibility_primary_reciprocal);
  
  // Calculate terms for eligibility trace
  int32_t eligibility_primary_term = BCPNN_FIXED_MUL_16X16(last_spike_eligility_constant, primary_decay);
  int32_t eligibility_decay_term = BCPNN_FIXED_MUL_16X16(last_event.eligibility_trace - last_spike_eligility_constant, eligibility_decay);
  
  int32_t new_eligibility_trace = eligibility_primary_term + eligibility_decay_term;
  
  plastic_runtime_log_info("\t\tbcpnn_add_spike: delta_time:%u, new_primary_trace:%d, new_eligibility_trace:%d\n", delta_time, new_primary_trace, new_eligibility_trace);
  
  // Return new trace structure with decayed trace values with energy for new spike added
  return (bcpnn_event_t){ .time = spike_time, .primary_trace = new_primary_trace, .eligibility_trace = new_eligibility_trace };
}
//---------------------------------------
static inline deferred_update_state_t bcpnn_apply_deferred_spike(uint32_t current_time, int16_t primary_trace,
                                                                 uint32_t other_trace_lead_time, int16_t other_primary_trace,
                                                                 deferred_update_state_t previous_state)
{
  // Get time since last correlation
  uint32_t delta_time = current_time - previous_state.time;
  
  // Lookup exponential decay over delta-time with both time constants
  int32_t primary_decay = BCPNN_DECAY_LOOKUP_PRIMARY(delta_time);
  int32_t two_primary_decay = BCPNN_DECAY_LOOKUP_PRIMARY(delta_time * 2);
  int32_t eligibility_decay = BCPNN_DECAY_LOOKUP_ELIGIBILITY(delta_time);
  int32_t lead_primary_decay = BCPNN_DECAY_LOOKUP_PRIMARY(other_trace_lead_time);
  
  int32_t other_lead_decay = BCPNN_FIXED_MUL_16X16(other_primary_trace, lead_primary_decay);
  int32_t correlated_numerator = BCPNN_FIXED_MUL_16X16(other_lead_decay, primary_trace);
  int32_t additive_epsilon_numerator = BCPNN_FIXED_MUL_16X16(plasticity_region_data.epsilon, other_lead_decay + primary_trace);
  
  int32_t correlated_constant = BCPNN_FIXED_MUL_16X16(correlated_numerator, plasticity_region_data.two_eligibility_primary_reciprocal);
  int32_t additive_epsilon_constant = BCPNN_FIXED_MUL_16X16(additive_epsilon_numerator, plasticity_region_data.eligibility_primary_reciprocal);
 
  int32_t eligibility_constant = previous_state.correlated_eligibility_trace - additive_epsilon_constant - correlated_constant;
  
  // Conbine all together into new correlated eligibility trace value
  int32_t new_correlated_elibility_trace = BCPNN_FIXED_MUL_16X16(additive_epsilon_constant, primary_decay)
    + BCPNN_FIXED_MUL_16X16(correlated_constant, two_primary_decay) + BCPNN_FIXED_MUL_16X16(eligibility_constant, eligibility_decay);
  
  // Build new trace structure and return
  return (deferred_update_state_t){ .time = current_time, .correlated_eligibility_trace = new_correlated_elibility_trace };
}

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline pair64_u bcpnn_update_synapse_correlation(uint32_t last_update_time, uint32_t delay, int32_t last_correlated_eligibility, 
  const pre_synaptic_event_history_t *pre_synaptic_event_history, uint32_t post_synaptic_neuron_index)
{
  // Get the pre-synaptic event prior to the window and the one next within it
  uint32_t next_pre_synaptic_event_index;
  uint32_t next_pre_synaptic_event_time;
  pre_synaptic_event_t last_pre_synaptic_event;
  pre_synaptic_event_find_first(pre_synaptic_event_history, last_update_time, delay, &next_pre_synaptic_event_index, &next_pre_synaptic_event_time, &last_pre_synaptic_event);
  
  // Get time and index of first post-synaptic event that occurs in the time window between the last update time of this synaptic row and the current time
  uint32_t next_post_synaptic_event_time;
  uint32_t next_post_synaptic_event_index;
  post_synaptic_event_t last_post_synaptic_event;
  post_synaptic_event_find_first(post_synaptic_neuron_index, last_update_time, &next_post_synaptic_event_index, &next_post_synaptic_event_time, &last_post_synaptic_event);
  
  // Create deferred update state structures
  deferred_update_state_t deferred_update_state = { .correlated_eligibility_trace = last_correlated_eligibility };
  
  // If the last pre-synaptic event processed was after the last post-synaptic event
  if(last_pre_synaptic_event.time > last_post_synaptic_event.time)
  {
    // Update the last post-synaptic event to the time of the last pre-synaptic event
    last_post_synaptic_event.trace.primary = bcpnn_update_primary_trace(last_pre_synaptic_event.time, last_post_synaptic_event.time, last_post_synaptic_event.trace.primary);
    last_post_synaptic_event.time = last_pre_synaptic_event.time;
    
    // The time of the last pre-synaptic event is therefore the time the correlation trace was last updated
    deferred_update_state.time = last_pre_synaptic_event.time;
  }
  // Otherwise, if the last post-synaptic event processed was after the last pre-synaptic event
  else if(last_post_synaptic_event.time > last_pre_synaptic_event.time)
  {
    // Update the last pre-synaptic event to the time of the last post-synaptic event
    last_pre_synaptic_event.trace.primary = bcpnn_update_primary_trace(last_post_synaptic_event.time, last_pre_synaptic_event.time, last_pre_synaptic_event.trace.primary);
    last_pre_synaptic_event.time = last_post_synaptic_event.time;
    
    // The time of the last post-synaptic event is therefore the time the correlation trace was last updated
    deferred_update_state.time = last_post_synaptic_event.time;
  }
  // Otherwise, both the traces were updated at the same time so can
  else
  {
    deferred_update_state.time = last_post_synaptic_event.time;
  }
  
  plastic_runtime_log_info("\tPerforming deferred synapse update at time:%u - last_post_synaptic_event.time:%u, last_pre_synaptic_event.time:%u(delayed), next_post_synaptic_event_time:%u, next_pre_synaptic_event_time:%u(delayed)\n",
    time, last_post_synaptic_event.time, last_pre_synaptic_event.time, next_post_synaptic_event_time, next_pre_synaptic_event_time);
  
  // While any pre or post-synaptic events remain
  while(next_pre_synaptic_event_index != UINT32_MAX || next_post_synaptic_event_index != UINT32_MAX)
  {
    // If next pre-synaptic event occurs before the next post-synaptic event
    // **NOTE** If next pre-synaptic event time's UINT32_MAX, this will never be true and due to loop conditions, both will never be UINT32_MAX!
    if(next_pre_synaptic_event_time <= next_post_synaptic_event_time)
    {
      plastic_runtime_log_info("\t\tApplying pre-synaptic event at time:%u\n", next_pre_synaptic_event_time);
      
      // Update correlation based on the last 
      deferred_update_state = bcpnn_apply_deferred_spike(next_pre_synaptic_event_time, last_pre_synaptic_event.trace.primary,
        deferred_update_state.time - last_post_synaptic_event.time, last_post_synaptic_event.trace.primary,
        deferred_update_state);
        
      // Update last pre-synaptic event to point to new event we're processing, updating time to delayed version
      last_pre_synaptic_event.trace = pre_synaptic_event_history->traces[next_pre_synaptic_event_index];
      last_pre_synaptic_event.time = next_pre_synaptic_event_time;
      
      // Go onto next pre-synaptic event
      pre_synaptic_event_find_next(pre_synaptic_event_history, delay, next_pre_synaptic_event_index, 
        &next_pre_synaptic_event_index, &next_pre_synaptic_event_time);
    }
    
    // Otherwise, if the next post-synaptic event occurs before the next pre-synaptic event
    if(next_post_synaptic_event_time <= next_pre_synaptic_event_time && next_post_synaptic_event_time != UINT32_MAX)
    {
      plastic_runtime_log_info("\t\tApplying post-synaptic event at time:%u\n", next_post_synaptic_event_time);
      
      // Update correlation based on the last 
      deferred_update_state = bcpnn_apply_deferred_spike(next_post_synaptic_event_time, last_post_synaptic_event.trace.primary,
        deferred_update_state.time - last_pre_synaptic_event.time, last_pre_synaptic_event.trace.primary,
        deferred_update_state);
      
      // Update last post-synaptic trace parameters
      last_post_synaptic_event.trace = post_synaptic_event_history_traces[post_synaptic_neuron_index][next_post_synaptic_event_index];
      last_post_synaptic_event.time = post_synaptic_event_history_times[post_synaptic_neuron_index][next_post_synaptic_event_index];
      
      // Go onto next post-synaptic event
      post_synaptic_event_find_next(post_synaptic_neuron_index, next_post_synaptic_event_index, 
        &next_post_synaptic_event_index, &next_post_synaptic_event_time);
    }
  }

  // If the last pre-synaptic event processed was after the last post-synaptic event, update post synaptic eligibility trace to this time
  int final_pre_synaptic_eligibility;
  int final_post_synaptic_eligibility;
  if(last_pre_synaptic_event.time > last_post_synaptic_event.time)
  {
    final_pre_synaptic_eligibility = last_pre_synaptic_event.trace.eligibility;
    final_post_synaptic_eligibility = bcpnn_update_eligibility_trace(deferred_update_state.time, last_post_synaptic_event.time, last_post_synaptic_event.trace.primary, post_synaptic_eligibility[neuron_index]);
  }
  // Otherwise, if the last post-synaptic event processed was after the last pre-synaptic event, update pre synaptic eligibility trace to this time
  else if(last_post_synaptic_event.time > last_pre_synaptic_event.time)
  {
    final_post_synaptic_eligibility = post_synaptic_eligibility[neuron_index];
    final_pre_synaptic_eligibility = bcpnn_update_eligibility_trace(deferred_update_state.time, last_pre_synaptic_event.time, last_pre_synaptic_event.trace.primary, last_pre_synaptic_event.trace.eligibility);
  }
  // Otherwise, both are up to date
  else
  {
    final_pre_synaptic_eligibility = last_pre_synaptic_event.trace.eligibility;
    final_post_synaptic_eligibility = post_synaptic_eligibility[neuron_index];
  }

  // Take logs of all three final eligibility traces
  int32_t log_pre_synaptic = bcpnn_fractional_ln(final_pre_synaptic_eligibility);
  int32_t log_post_synaptic = bcpnn_fractional_ln(final_post_synaptic_eligibility);
  int32_t log_correlation = bcpnn_fractional_ln(deferred_update_state.correlated_eligibility_trace);
  
  // Calculate bayesian weight (using log identities to remove divide)
  int32_t weight = log_correlated - (log_pre_synaptic + log_post_synaptic);
  
  // Return pair containing new eligibility value and weight
  return pair_int32(deferred_update_state.correlated_eligibility_trace, weight);
}

//---------------------------------------
// PACMAN memory region reading
//---------------------------------------
void initialise_plasticity_buffers()
{
  log_info("initialise_plasticity_buffers: starting");
  
  // Allocate memory for post-synaptic eligibility traces
  // **NOTE**These aren't needed for correlation so don't need to be stored per-spike
  post_synaptic_eligibility = (int16_t*)spin1_malloc(num_neurons * sizeof(int16_t));
  
  // If allocation's succeeded
  if(post_synaptic_eligibility != NULL)
  {
    // Copy initial eligibility value into each neuron's trace
    for(uint32_t n = 0; n < num_neurons; n++)
    {
      post_synaptic_eligibility[n] = plasticity_region_data.initial_eligibility;
    }
  }
  else
  {
    sentinel("Unable to allocate post-synaptic eligibility structures - Out of DTCM");
  }
  
  // Initialise memory for post-synaptic events
  initialise_post_synaptic_event_buffers();
  
  log_info("initialise_plasticity_buffers: completed successfully");
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline int16_t* plastic_correlated_eligibilities(address_t plastic)
{
  const uint32_t pre_synaptic_event_history_size_words = sizeof(pre_synaptic_event_history_t) / sizeof(uint32_t);
  COMPILE_TIME_ASSERT(pre_synaptic_event_history_size_words * sizeof(uint32_t) == sizeof(pre_synaptic_event_history_t), pre_synaptic_event_history_t_should_be_word_padded)
  
  return (int16_t*)(&plastic[pre_synaptic_event_history_size_words]); 
}
//---------------------------------------
static inline pre_synaptic_event_history_t *plastic_event_history(address_t plastic)
{
  return (pre_synaptic_event_history_t*)(&plastic[0]);
}
//---------------------------------------
void plasticity_process_post_synaptic_event(uint32_t neuron_index)
{
#ifdef DEBUG
  plastic_runtime_log_enabled = false;
#endif  // DEBUG
  
  plastic_runtime_log_info("Processing post-synaptic event at time:%u\n", time);
  
  // Get last post-synaptic event. If there are none, initialise primary trace to initial value and last_spike_time to zero
  bcpnn_event_t last_post_synaptic_event = bcpnn_post_synaptic_event_last(neuron_index);
  
  // Apply affect of new spike to this
  bcpnn_event_t new_post_synaptic_event = bcpnn_add_spike(time, last_post_synaptic_event);
  
  // Append primary trace value to history and store new eligibility trace
  post_synaptic_event_add(neuron_index, new_post_synaptic_event.time, (post_synaptic_trace_entry_t){ .primary = new_post_synaptic_event.primary_trace });
  post_synaptic_eligibility[neuron_index] = new_post_synaptic_event.eligibility_trace;
}
//---------------------------------------
void process_plastic_synapses(address_t plastic, address_t fixed, ring_entry_t *ring_buffer)
{
#ifdef DEBUG
  plastic_runtime_log_enabled = false;
#endif  // DEBUG
  
  // Extract seperate arrays of weights (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  int16_t *correlated_eligibilities = plastic_correlated_eligibilities(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);
  
  // Get event history from synaptic row
  pre_synaptic_event_history_t *event_history = plastic_event_history(plastic);
  
  // Get last pre-synaptic event from event history
  // **NOTE** at this level we don't care about individual synaptic delays
  bcpnn_event_t last_pre_synaptic_event = bcpnn_pre_synaptic_event_last(event_history);
  
  // Loop through plastic synapses
  for ( ; plastic_synapse > 0; plastic_synapse--) 
  {
    // Get next weight and control word (autoincrementing control word)
    int32_t correlated_eligibility = *correlated_eligibilities;
    uint32_t control_word = *control_words++;
    
    // Extract control-word components
    // **NOTE** cunningly, control word is just the same as lower 
    // 16-bits of 32-bit fixed synapse so same functions can be used
    uint32_t delay = sparse_delay(control_word);
    uint32_t index = sparse_type_index(control_word);
    
    // Update synapse weight
    pair64_u updated_synapse = bcpnn_update_synapse_correlation(last_pre_synaptic_event.time, delay, correlated_eligibility, event_history, index);
    
    // Convert into ring buffer offset
    //uint32_t offset = offset_sparse(delay + time, index);
    
    // Add weight to ring-buffer entry
    // **NOTE** Dave suspects that this could be a potential location for overflow
    //ring_buffer[offset] += weight;
    
    // Write back updated weight to plastic region
    // **THINK** is this actually the right operator-mess to store and autoincrement
    *correlated_eligibilities++ = updated_correlated_eligibility;
  }
  
  plastic_runtime_log_info("Processing pre-synaptic event at time:%u\n", time);
  
  // Get new event from learning rule
  pre_synaptic_trace_entry_t new_pre_synaptic_trace_entry = stdp_trace_rule_add_pre_synaptic_spike(time, last_pre_synaptic_event.time, last_pre_synaptic_event.trace);
  
  // Add pre-synaptic event to history
  pre_synaptic_event_add(event_history, time, new_pre_synaptic_trace_entry);
}
//---------------------------------------
bool plasticity_region_filled (uint32_t* address, uint32_t flags)
{
  use(flags);
  
  log_info("plasticity_region_filled: starting");
  log_info("\tBCPNN rule");
  // **TODO** assert number of neurons is less than max
  
  // Copy plasticity region data from address
  // **NOTE** this seems somewhat safer than relying on sizeof
  plasticity_region_data.eligibility_primary_reciprocal = address[0];
  plasticity_region_data.two_eligibility_primary_reciprocal = address[1];
  plasticity_region_data.log2_to_natural_log_convert = address[2];
  plasticity_region_data.epsilon = address[3];
  plasticity_region_data.epsilon_squared = address[4];
  plasticity_region_data.spike_height = address[5];
  plasticity_region_data.initial_primary = address[6];
  plasticity_region_data.initial_eligibility = address[7];
  plasticity_region_data.weight_gain = address[8];
  
  log_info("\teligibility_primary_reciprocal:%d, two_eligibility_primary_reciprocal:%d, log2_to_natural_log_convert:%d, epsilon:%d, epsilon_squared:%d, spike_height:%d, initial_primary:%d, initial_eligibility:%d, weight:%d", 
      plasticity_region_data.eligibility_primary_reciprocal, plasticity_region_data.two_eligibility_primary_reciprocal, plasticity_region_data.log2_to_natural_log_convert, plasticity_region_data.epsilon,
      plasticity_region_data.epsilon_squared, plasticity_region_data.spike_height, plasticity_region_data.initial_primary, plasticity_region_data.initial_eligibility);
  
  // Copy LUTs from following memory
  address_t lut_address = copy_int16_lut(&address[9], BCPNN_PRIMARY_SIZE, &bcpnn_primary_lookup[0]);
  lut_address = copy_int16_lut(lut_address, BCPNN_ELIGIBILITY_SIZE, &bcpnn_eligibility_lookup[0]);
  lut_address = copy_int16_lut(lut_address, BCPNN_FRACTIONAL_LOG_SIZE, &bcpnn_fractional_log_lookup[0]);
  
  log_info("plasticity_region_filled: completed successfully");
  
  return true;
}
//---------------------------------------
#ifdef DEBUG
void print_plastic_synapses(address_t plastic, address_t fixed)
{
  // Extract seperate arrays of weights (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  const int16_t *correlated_eligibilities = plastic_correlated_eligibilities(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);
  const pre_synaptic_event_history_t *event_history = plastic_event_history(plastic);
  
  printf ("Plastic region %u synapses pre-synaptic event buffer start index:%u count:%u:\n", plastic_synapse, event_history->start_index, event_history->count);
  
  // Loop through plastic synapses
  for (uint32_t i = 0; i < plastic_synapse; i++) 
  {
    // Get next weight and control word (autoincrementing control word)
    int32_t correlated_eligibility = *correlated_eligibilities++;
    uint32_t control_word = *control_words++;
    
    printf ("%08x [%3d: (e: %d d: %2u, %c, n = %3u)] - {%08x %08x}\n", 
            control_word, i, correlated_eligibility, 
            sparse_delay(control_word),
            (sparse_type(control_word)==0)? 'X': 'I',
            sparse_index(control_word),
            SYNAPSE_DELAY_MASK,
            SYNAPSE_TYPE_INDEX_BITS
    );
  }
}
#endif  // DEBUG
