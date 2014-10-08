#include "../common/common-impl.h"
#include <string.h>

// Globals
static uint32_t time;
static bool apply_prefix;
static uint32_t prefix;
static uint32_t key_space;
static uint32_t mask;

typedef struct
{
  uint16_t event;
  uint16_t payload;
} event16_t;

typedef struct
{
  uint32_t event;
  uint32_t payload;
} event32_t;

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;
  
  if ((simulation_ticks != UINT32_MAX) 
	&& (time >= simulation_ticks + timer_period))
  {
    log_info("Simulation complete.\n");
    spin1_exit(0);
    return;
  }
}

void process_16_bit_packets (void* event_pointer, uint8_t length,
							 uint32_t pkt_prefix, bool payload)
{
  uint32_t i;
  uint16_t *events_array = (uint16_t *) event_pointer;
  event16_t *events_struct = (event16_t *) event_pointer;
  
  if (!payload)
  {
	for (i = 0; i < length; i++)
	{
	  uint32_t key = (uint32_t) events_array[i];
	  key |= pkt_prefix;
	  
	  spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
	}
  }
  else
  {
	for (i = 0; i < length; i++)
	{
	  uint32_t payload = (uint32_t) events_struct[i].payload;
	  uint32_t key = (uint32_t) events_struct[i].event;
	  key |= pkt_prefix;
	  
	  spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
	}
  }
}

void process_32_bit_packets (void* event_pointer, uint8_t length, 
							 uint32_t pkt_prefix, bool payload)
{
  uint32_t i;
  
  if (!payload)
  {
	uint32_t *events = (uint32_t *) event_pointer;
	
	for (i = 0; i < length; i++)
	  spin1_send_mc_packet(events[i] | pkt_prefix, NULL, NO_PAYLOAD);
  }
  else
  {
	event32_t *events = (event32_t *) event_pointer;
	
	for (i = 0; i < length; i++)
	  spin1_send_mc_packet(events[i].event | pkt_prefix, events[i].payload, WITH_PAYLOAD);
  }
}

void sdp_packet_callback(uint mailbox, uint port)
{
  sdp_msg_t *msg = (sdp_msg_t *) mailbox;
  uint16_t *data_hdr = (uint16_t *) msg;
  uint16_t data_hdr_value = data_hdr[0];
  uint32_t pkt_prefix = 0;
  void *event_pointer = (void *) data_hdr + 1;
  
  use(port);
  
  bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
  bool pkt_format = (bool) (data_hdr_value >> 14 & 0x1);
  uint8_t pkt_type = (uint8_t) (data_hdr_value >> 12 & 0x3);
  uint8_t pkt_len = (uint8_t) (data_hdr_value & 0xFF) + 1;
  bool payload = (bool) (pkt_type & 0x1);
	
  if (pkt_apply_prefix)
  {
	uint16_t *prefix_ptr = data_hdr + 1;
	event_pointer = (void*) (data_hdr + 2);
	
	pkt_prefix = (uint32_t) prefix_ptr[0];
	
	if (pkt_format) pkt_prefix <<= 16;
  }
  
  if (pkt_type == 0 || pkt_type ==1)
	process_16_bit_packets (event_pointer, pkt_len, pkt_prefix, payload);
  else
	process_32_bit_packets (event_pointer, pkt_len, pkt_prefix, payload);
  
  //free the message to stop overlaod
  spin1_msg_free(msg);
}

bool multicast_source_data_filled(address_t base_address) {
  address_t region_address = region_start(1, base_address);

  // to write here retrieving the configuration of the population:
  // one 32 bit value which contains the three leftmost bits
  // Prefix, Format and Prefix Check
  // The lowest 16 bits are the prefix itself
  apply_prefix = region_address[0];
  prefix = region_address[1];
  key_space = region_address[2];
  mask = region_address[3];

  return (true);
}

bool system_load_dtcm(void) {

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  system_load_params(region_start(0, address));

  uint32_t version;
  uint32_t flags = 0;
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
