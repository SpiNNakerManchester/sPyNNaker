#include "../common/common-impl.h"
#include <string.h>

// Counters
#define N_COUNTERS       6
#define	MOTION_FORWARD   0x01
#define MOTION_BACK	     0x02
#define	MOTION_RIGHT     0x03
#define	MOTION_LEFT	     0x04
#define	MOTION_CLOCKWISE 0x05
#define	MOTION_C_CLKWISE 0x06
#define NEURON_ID_MASK   0x7FF

// Globals
static uint32_t time;
static uint32_t *counters;
static uint32_t *last_speed;
static uint32_t key;
static uint32_t speed;
static uint32_t sample_time;
static uint32_t update_time;
static uint32_t delay_time;
static int delta_threshold;
static uint32_t continue_if_not_different;

static inline void send(uint32_t direction, uint32_t speed) {
	uint32_t direction_key = direction | key;
	while (!spin1_send_mc_packet(direction_key, speed, WITH_PAYLOAD)) {
		spin1_delay_us(1);
	}
	if (delay_time > 0) {
		spin1_delay_us(delay_time);
	}
}

static inline void do_motion(uint32_t direction_index, uint32_t opposite_index,
		const char *direction, const char *opposite) {
  int direction_count = (int) counters[direction_index - 1];
  int opposite_count = (int) counters[opposite_index - 1];
  int delta = direction_count - opposite_count;
  log_info("%s = %d, %s = %d, delta = %d, threshold = %u", direction,
		  direction_count, opposite, opposite_count, delta, delta_threshold);
  if (delta >= delta_threshold)
  {
	log_info("Moving %s", direction);
	last_speed[direction_index - 1] = speed;
	last_speed[opposite_index - 1] = 0;
	send(direction_index, speed);
  }
  else if (delta <= -delta_threshold)
  {
	log_info("Moving %s", direction);
	last_speed[direction_index - 1] = 0;
	last_speed[opposite_index - 1] = speed;
    send(opposite_index, speed);
  }
  else if (continue_if_not_different == 0)
  {
    log_info("Motion is indeterminate in %s-%s direction", direction, opposite);
    last_speed[direction_index - 1] = 0;
    last_speed[opposite_index - 1] = 0;
    send(direction_index, 0);
  }
}

static inline void do_update(uint32_t direction_index, uint32_t opposite_index,
		const char *direction, const char *opposite) {
  int direction_speed = (int) last_speed[direction_index - 1];
  int opposite_speed = (int) last_speed[opposite_index - 1];
  int delta = direction_speed - opposite_speed;
  if (delta > 0)
  {
	log_info("Resending %s = %d", direction, direction_speed);
	send(direction_index, direction_speed);
  }
  else if (delta < 0)
  {
	log_info("Resending %s = %d", opposite, opposite_speed);
	send(opposite_index, opposite_speed);
  }
  else
  {
	log_info("Resending No Motion in the %s-%s direction", direction, opposite);
	send(direction_index, 0);
  }
}

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;
  
  log_info("Timer tick %d", time);

#ifdef DEBUG
  if (time == 0)
  {
	log_info("Key = %d, speed = %d, sample_time = %d, update_time = %d, delay_time = %d, delta_threshold = %d, continue_if_not_different = %d",
				key, speed, sample_time, update_time, delay_time, delta_threshold, continue_if_not_different);
  }
#endif

  if (simulation_ticks != UINT32_MAX && time == simulation_ticks + timer_period)
  {
    log_info("Simulation complete.\n");
    spin1_exit(0);
    return;
  }
  
  // Process the incoming spikes
  spike_t s;
  uint32_t nid;
  while (next_spike (&s))
  {
    nid = (s & NEURON_ID_MASK);

    if (nid < N_COUNTERS) {
      counters[nid] += 1;
    } else {
       log_info("Received spike from unknown neuron %d", nid);
    }
  }

  // Work out if there is any motion
  if ((time % sample_time) == 0)
  {

	// Do motion in pairs
	do_motion(MOTION_FORWARD, MOTION_BACK, "Forwards", "Backwards");
	do_motion(MOTION_LEFT, MOTION_RIGHT, "Left", "Right");
	do_motion(MOTION_CLOCKWISE, MOTION_C_CLKWISE, "Clockwise",
			"Anti-clockwise");

	// Reset the counters
	for (uint32_t i = 0; i < N_COUNTERS; i++)
	{
	  counters[i] = 0;
	}
  }
  else if ((time % update_time) == 0)
  {

	// Do updates in pairs
    do_update(MOTION_FORWARD, MOTION_BACK, "Forwards", "Backwards");
    do_update(MOTION_LEFT, MOTION_RIGHT, "Left", "Right");
    do_update(MOTION_CLOCKWISE, MOTION_C_CLKWISE, "Clockwise",
		"Anti-clockwise");
  }
}

bool robot_source_data_filled(address_t base_address) {
	address_t region_address = region_start(1, base_address);
	log_info("Reading data from 0x%.8x", region_address);
	key = region_address[0];
	speed = region_address[1];
	sample_time = region_address[2];
	update_time = region_address[3];
	delay_time = region_address[4];
	delta_threshold = region_address[5];
	continue_if_not_different = region_address[6];

	// Allocate the space for the schedule
	counters = (uint32_t*) spin1_malloc(N_COUNTERS * sizeof(uint32_t));
	last_speed = (uint32_t*) spin1_malloc(N_COUNTERS * sizeof(uint32_t));

	for (uint32_t i = 0; i < N_COUNTERS; i++)
	{
	  counters[i] = 0;
	  last_speed[i] = 0;
	}

	return (true);
}

void incoming_spike_callback (uint key, uint payload)
{
  use(payload);

#ifdef DEBUG
  log_info("Received spike %x", key);
#endif // DEBUG

#ifdef SPIKE_DEBUG
  io_printf(IO_BUF, "Received spike %x at %d\n", key, time);
#endif // SPIKE_DEBUG

  // If there was space to add spike to incoming spike queue
  add_spike(key);

}

bool system_load_dtcm(void) {

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();
  system_load_params(region_start(0, address));

  uint32_t version;
  uint32_t flags   = 0;
  if(!system_header_filled (address, &version, flags))
  {
	return (false);
  }
  if (!robot_source_data_filled(address)) {
	return (false);
  }

  return (true);
}

// Entry point
void c_main (void)
{
  // Configure system
  io_printf(IO_BUF, "Initializing robot code\n");
  system_load_dtcm();

/*
  // Configure lead app-specific stuff
  if(leadAp)
  {
    system_lead_app_configured();
  }
*/

  // Initialize the incoming spike buffer
  initialize_spike_buffer (8192);

  // Set timer_callback
  spin1_set_timer_tick(timer_period);
  
  // Register callbacks
  spin1_callback_on (MC_PACKET_RECEIVED, incoming_spike_callback, -1);
  spin1_callback_on (TIMER_TICK,         timer_callback,           2);
  
  log_info("Starting");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();
}
