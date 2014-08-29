#include "../common/common-impl.h"
#include <string.h>

// Globals
static uint32_t time;
static uint32_t *schedule;
static uint32_t schedule_size;
static uint32_t next_pos;


// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;
  
  if ((next_pos >= schedule_size)
		  && (simulation_ticks != UINT32_MAX)
		  && (time >= simulation_ticks + timer_period))
  {
    log_info("Simulation complete.\n");
    spin1_exit(0);
    return;
  }
  
  if ((next_pos < schedule_size) && schedule[next_pos] == time) {
	  uint32_t with_payload_count = schedule[++next_pos];
	  log_info("Sending %d packets with payloads at time %d",
			  with_payload_count, time);
	  for (uint32_t i = 0; i < with_payload_count; i++) {
		  uint32_t key = schedule[++next_pos];
		  uint32_t payload = schedule[++next_pos];
		  //check for delays and repeats
		  uint32_t delay_and_repeat_data = schedule[++next_pos];
		  if (delay_and_repeat_data != 0){
		      uint16_t repeat = delay_and_repeat_data >> 8;
		      uint16_t delay = delay_and_repeat_data & 0x0000ffff;
		      log_info("Sending %d, %d at time %d with %d repeats and %d delay ",
		           key, payload, time, repeat, delay);
		      for(uint16_t repeat_count=0; repeat_count < repeat; repeat_count++) {
		          spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
		          if(delay > 0){// if the delay is 0, dont call delay
                      spin1_delay_us(delay);
                }
            }
		  }
		  else{//if no repeats, then just sned the message
		    spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
		  }
	  }

	  uint32_t without_payload_count = schedule[++next_pos];
	  log_info("Sending %d packets without payloads at time %d",
			  without_payload_count, time);
	  for (uint32_t i = 0; i < without_payload_count; i++) {
		  uint32_t key = schedule[++next_pos];
		  log_info("Sending %d", key);
		  //check for delays and repeats
		  uint32_t delay_and_repeat_data = schedule[++next_pos];
		  if (delay_and_repeat_data != 0){
		      uint16_t repeat = delay_and_repeat_data >> 8;
		      uint16_t delay = delay_and_repeat_data & 0x0000ffff;
		      for(uint16_t repeat_count=0; repeat_count < repeat; repeat_count++) {
		          spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
		          if(delay > 0){// if the delay is 0, dont call delay
                      spin1_delay_us(delay);
                }
            }
		  }
		  else{//if no repeats, then just sned the message
		    spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
		  }

	  }
	  ++next_pos;

	  if (next_pos < schedule_size) {
	      log_info("Next packets will be sent at %d", schedule[next_pos]);
	  } else {
		  log_info("End of Schedule");
	  }
  }
}

void sdp_packet_callback(uint mailbox, uint port)
{
  sdp_msg_t *msg = (sdp_msg_t *) mailbox;
  uint32_t key = msg->arg1;
  if (msg->cmd_rc == NO_PAYLOAD) {
	spin1_send_mc_packet(key, 0, NO_PAYLOAD);
  } else if (msg->cmd_rc == WITH_PAYLOAD) {
	uint32_t payload = msg->arg2;
	spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
  }
  //free the message to stop overlaod
  spin1_msg_free(msg);
}

bool multicast_source_data_filled(address_t base_address) {
	address_t region_address = region_start(2, base_address);
	schedule_size = region_address[0] >> 2;

	// Allocate the space for the schedule
	schedule = (uint32_t*) spin1_malloc(schedule_size * sizeof(uint32_t));
	memcpy(schedule, &region_address[1], schedule_size * sizeof(uint32_t));

	next_pos = 0;
	log_info("Schedule starts at time %d", schedule[0]);

	return (true);
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
  if (!multicast_source_data_filled(address)) {
	return (false);
  }

  return (true);
}

// Entry point
void c_main (void)
{
  // Configure system
  system_load_dtcm();
 
  // Configure lead app-specific stuff
  if(leadAp)
  {
    system_lead_app_configured();
  }
  
  // Set timer_callback
  spin1_set_timer_tick(timer_period);
  
  // Register callbacks
  spin1_callback_on (SDP_PACKET_RX,      sdp_packet_callback,  -1);
  spin1_callback_on (TIMER_TICK,         timer_callback,       2);
  
  log_info("Starting");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();
}
