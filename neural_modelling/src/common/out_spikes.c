#include "common-impl.h"

// Globals
bit_field_t out_spikes;

static size_t out_spikes_size;

void reset_out_spikes (void) { clear_bit_field (out_spikes, out_spikes_size); }

void initialize_out_spikes (size_t max_spike_sources)
{
  out_spikes_size = get_bit_field_size(max_spike_sources);
  log_info("Out spike size is %u words, allowing %u spike sources", out_spikes_size, max_spike_sources);
  
  out_spikes = (bit_field_t)sark_alloc (out_spikes_size * sizeof (uint32_t), 1);
  reset_out_spikes ();
}

void record_out_spikes (void)
{
  // If we should record the spike history, copy out-spikes to the appropriate recording channel
  if(system_data_test_bit(e_system_data_record_spike_history))
  {
	  recording_record(e_recording_channel_spike_history, out_spikes, out_spikes_size * sizeof (uint32_t));
  }
}

bool empty_out_spikes (void)
{ 
	return (empty_bit_field (out_spikes, out_spikes_size)); 
  
}

bool nonempty_out_spikes (void)
{ 
	return (nonempty_bit_field (out_spikes, out_spikes_size)); 
  
}

bool out_spike_test (index_t n)
{ 
  return (bit_field_test (out_spikes, n)); 
}

#ifdef DEBUG
void print_out_spikes (void)
{
  printf ("out_spikes:\n");
  
  if (nonempty_out_spikes()) {
    printf ("-----------\n");
    print_bit_field (out_spikes, out_spikes_size);
    printf ("-----------\n");
  }
}
#else
void print_out_spikes(void) {
	skip();
}
#endif  // DEBUG
