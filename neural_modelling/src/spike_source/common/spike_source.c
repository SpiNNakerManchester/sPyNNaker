#include "spike_source_impl.h"

#include <string.h>

// Globals
uint32_t key = 0;
uint32_t num_spike_sources = 0;

static uint32_t time;

bool load_dtcm ()
{
  log_info("load_dtcm: started");
  
  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();
  
  uint32_t version;
  uint32_t flags   = 0;
  if(!system_header_filled (address, &version, flags))
  {
    return (false);
  }
  
  // Read system region
  uint32_t spike_history_recording_region_size, neuron_potentials_recording_region_size, neuron_gsyns_recording_region_size;
  if (!system_data_filled (region_start(0, address), flags, &spike_history_recording_region_size, &neuron_potentials_recording_region_size, &neuron_gsyns_recording_region_size))
    return (false);
  
  // Perform spike-source specific loading routine
  spike_source_data_filled(address, flags, spike_history_recording_region_size, neuron_potentials_recording_region_size, neuron_gsyns_recording_region_size);
  
  log_info("load_dtcm: completed successfully");
  
  return (true);
}

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;
  
  log_info("Timer tick %u", time);
  
  // If a fixed number of simulation ticks are specified and these have passed
  if (simulation_ticks != UINT32_MAX && time >= simulation_ticks)
  {
    log_info("Simulation complete.\n");
    
    // Finalise any recordings that are in progress, writing back the final amounts of samples recorded to SDRAM
    recording_finalise();
    spin1_exit(0);
  }
  
  // Generate spikes
  spike_source_generate(time);
  
  // Record output spikes if required
  record_out_spikes();

  if (nonempty_out_spikes ()) 
  {

#ifdef DEBUG
    print_out_spikes ();
#endif // DEBUG

#ifdef SPIKE_SOURCE_SEND_OUT_SPIKES
    for (index_t i = 0; i < num_spike_sources; i++)
    {
      if (out_spike_test (i))
      {
        log_info("Sending spike packet %x", key | i);
        spin1_send_mc_packet(key | i, NULL, NO_PAYLOAD);
        spin1_delay_us(1);
      }
    }
#endif  // SPIKE_SOURCE_SEND_OUT_SPIKES

    reset_out_spikes ();
  }
}

// Entry point
void c_main (void)
{
  // Load DTCM data
  load_dtcm();

/*
  // Configure lead app-specific stuff
  if(leadAp)
  {
    system_lead_app_configured();
  }
*/

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;

  // Initialize out spikes buffer to support number of neurons
  initialize_out_spikes (num_spike_sources);
  
  // Set timer tick (in microseconds)
  spin1_set_timer_tick (timer_period);
  
  // Register callbacks
  spin1_callback_on (TIMER_TICK, timer_callback, 2);
  spin1_callback_on (DMA_TRANSFER_DONE, spike_source_dma_callback, 0);
  
  log_info("Starting");
  system_runs_to_completion();
}
