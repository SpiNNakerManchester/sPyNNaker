#include "../common/common-impl.h"

#include <string.h>

// Globals
static uint32_t time = UINT32_MAX;

static bool load_dtcm ()
{
  log_info("load_dtcm: started");

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  system_load_params(region_start(0, address));
  log_info("load_dtcm: completed successfully");

  return (true);
}

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

    // Finalise any recordings that are in progress, writing back the final
    // amounts of samples recorded to SDRAM
    recording_finalise();
    spin1_exit(0);
  }
}

// Entry point
void c_main (void)
{
  // Load DTCM data
  load_dtcm();

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;

  // Set timer tick (in microseconds)
  spin1_set_timer_tick (timer_period);

  // Register callbacks
  spin1_callback_on (TIMER_TICK, timer_callback, 2);

  log_info("Starting");
  system_runs_to_completion();
}
