#include "../common/common-impl.h"
#include <string.h>

// Globals
static uint32_t time;
static bool apply_prefix;
static bool check;
static uint32_t prefix;
static uint32_t key_space;
static uint32_t mask;
static uint32_t incorrect_keys;
static uint32_t key_left_shift;

typedef struct
{
  uint16_t event;
  uint16_t payload;
} event16_t;

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
	io_printf(IO_BUF, "Incorrect keys discarded: %d\n", incorrect_keys);
	spin1_exit(0);
	return;
  }
}

void process_16_bit_packets (void* event_pointer, bool pkt_format,
							 uint32_t length, uint32_t pkt_prefix,
							 uint32_t pkt_payload_prefix, bool payload,
							 bool pkt_payload_prefix_apply)
{
  uint32_t i;

/*
  io_printf (IO_BUF, "process_16_bit_packets\n");
  io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);
  io_printf (IO_BUF, "length: %d\n", length);
  io_printf (IO_BUF, "pkt_prefix: %08x\n", pkt_prefix);
  io_printf (IO_BUF, "pkt_payload_prefix: %08x\n", pkt_payload_prefix);
  io_printf (IO_BUF, "payload on: %d\n", payload);
  io_printf (IO_BUF, "pkt_format: %d\n", pkt_format);
*/

  if (!payload && !pkt_payload_prefix_apply)
  {
	uint16_t *events_array = (uint16_t *) event_pointer;
	
//	io_printf (IO_BUF, "no payload\n");
	
	for (i = 0; i < length; i++)
	{
//	  io_printf (IO_BUF, "process element: %d\n", i);
//	  io_printf (IO_BUF, "element: %08x\n", events_array[i]);
	  uint32_t key = (uint32_t) (events_array[i]);

	  if (!pkt_format) key <<= 16;
	  key |= pkt_prefix;

/*
	  io_printf (IO_BUF, "check: %d\n", check);
	  io_printf (IO_BUF, "key: %08x\n", key);
	  io_printf (IO_BUF, "mask: %08x\n", mask);
	  io_printf (IO_BUF, "key_space: %08x\n", key_space);
	  io_printf (IO_BUF, "test: %d\n", (check && ((key & mask) == key_space)));
*/

//	  io_printf (IO_BUF, "mc packet 16 key: %08x\n", key);

	  if ( (!check) || (check && ((key & mask) == key_space)))
	  {
//		io_printf (IO_BUF, "mc packet 16 key: %08x\n", key);
		spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
	  }
	  else
		incorrect_keys++;
	}
  }
  else if (!payload && pkt_payload_prefix_apply)
  {
	uint16_t *events_array = (uint16_t *) event_pointer;
	uint32_t payload = pkt_payload_prefix;

//	io_printf (IO_BUF, "no payload\n");

	for (i = 0; i < length; i++)
	{
//	  io_printf (IO_BUF, "process element: %d\n", i);
//	  io_printf (IO_BUF, "element: %08x\n", events_array[i]);
	  uint32_t key = (uint32_t) (events_array[i]);

	  if (!pkt_format) key <<= 16;
	  key |= pkt_prefix;

/*
	  io_printf (IO_BUF, "check: %d\n", check);
	  io_printf (IO_BUF, "key: %08x\n", key);
	  io_printf (IO_BUF, "mask: %08x\n", mask);
	  io_printf (IO_BUF, "key_space: %08x\n", key_space);
	  io_printf (IO_BUF, "test: %d\n", (check && ((key & mask) == key_space)));
*/

//	  io_printf (IO_BUF, "mc packet 16 key: %08x, payload: %08x\n", key, payload);

	  if ( (!check) || (check && ((key & mask) == key_space)))
	  {
//		io_printf (IO_BUF, "mc packet 16 key: %08x, payload: %08x\n", key, payload);
		spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
	  }
	  else
		incorrect_keys++;
	}
  }
  else
  {
	event16_t *events_struct = (event16_t *) event_pointer;
	
	for (i = 0; i < length; i++)
	{
	  uint32_t payload = (uint32_t) events_struct[i].payload;
	  uint32_t key = (uint32_t) events_struct[i].event;

	  if (!pkt_format) key <<= 16;
	  key |= pkt_prefix;
	  payload |= pkt_payload_prefix;

//	  io_printf (IO_BUF, "mc packet 16 key: %08x, payload: %08x\n", key, payload);

	  if ( (!check) || (check && ((key & mask) == key_space)))
	  {
//		io_printf (IO_BUF, "mc packet 16 key: %08x, payload: %08x\n", key, payload);
		spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
	  }
	  else
		incorrect_keys++;
	}
  }
}

void process_32_bit_packets (void* event_pointer,
							 uint32_t length, uint32_t pkt_prefix,
							 uint32_t pkt_payload_prefix, bool payload,
							 bool pkt_payload_prefix_apply)
{
  uint32_t i;

/*
  io_printf (IO_BUF, "process_32_bit_packets\n");
  io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);
  io_printf (IO_BUF, "length: %d\n", length);
  io_printf (IO_BUF, "pkt_prefix: %08x\n", pkt_prefix);
  io_printf (IO_BUF, "pkt_payload_prefix: %08x\n", pkt_payload_prefix);
  io_printf (IO_BUF, "payload: %d\n", payload);
  io_printf (IO_BUF, "pkt_payload_prefix_apply: %d\n", pkt_payload_prefix_apply);
*/

  if (!payload && !pkt_payload_prefix_apply)
  {
	uint16_t *events = (uint16_t *) event_pointer;

/*
	io_printf (IO_BUF, "case 1\n");
	io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);
	io_printf (IO_BUF, "events: %08x\n", (uint32_t) events);
	io_printf (IO_BUF, "no payload\n");
*/

	for (i = 0; i < (length << 1); i+=2)
	{
	  uint32_t key;
	  uint32_t temp1 = events[i];
	  uint32_t temp2 = events[i+1];

	  key = temp2 << 16 | temp1;
	  key |= pkt_prefix;

/*
	  io_printf (IO_BUF, "check: %d\n", check);
	  io_printf (IO_BUF, "key: %08x\n", key);
	  io_printf (IO_BUF, "mask: %08x\n", mask);
	  io_printf (IO_BUF, "key_space: %08x\n", key_space);
	  io_printf (IO_BUF, "test: %d\n", (check && ((key & mask) == key_space)));
*/

//	  io_printf (IO_BUF, "mc packet 32 key: %08x\n", key);

	  if ( (!check) || (check && ((key & mask) == key_space)))
	  {
//		io_printf (IO_BUF, "mc packet 32 key: %08x\n", key);
		spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
	  }
	  else
		incorrect_keys++;
	}
  }
  else if (!payload && pkt_payload_prefix_apply)
  {
	uint16_t *events = (uint16_t *) event_pointer;
	uint32_t payload = pkt_payload_prefix;

/*
	io_printf (IO_BUF, "case 2\n");
	io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);
	io_printf (IO_BUF, "events: %08x\n", (uint32_t) events);
	io_printf (IO_BUF, "no payload\n");
*/

	for (i = 0; i < (length << 1); i+=2)
	{
	  uint32_t key;
	  uint32_t temp1 = events[i];
	  uint32_t temp2 = events[i+1];

	  key = temp2 << 16 | temp1;
	  key |= pkt_prefix;

/*
	  io_printf (IO_BUF, "check: %d\n", check);
	  io_printf (IO_BUF, "key: %08x\n", key);
	  io_printf (IO_BUF, "mask: %08x\n", mask);
	  io_printf (IO_BUF, "key_space: %08x\n", key_space);
	  io_printf (IO_BUF, "test: %d\n", (check && ((key & mask) == key_space)));
*/

//	  io_printf (IO_BUF, "mc packet 32 key: %08x, payload: %08x\n", key, payload);

	  if ( (!check) || (check && ((key & mask) == key_space)))
	  {
//		io_printf (IO_BUF, "mc packet 32 key: %08x, payload: %08x\n", key, payload);
		spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
	  }
	  else
		incorrect_keys++;
	}
  }
  else
  {
	uint16_t *events = (uint16_t *) event_pointer;

//	io_printf (IO_BUF, "case 3\n");

	for (i = 0; i < (length << 2); i+=4)
	{
	  uint32_t key;
	  uint32_t payload;

	  uint32_t temp1 = events[i];
	  uint32_t temp2 = events[i+1];
	  key = temp2 << 16 | temp1;
	  key |= pkt_prefix;

	  temp1 = events[i+2];
	  temp2 = events[i+3];
	  payload = temp2 << 16 | temp1;
	  payload |= pkt_payload_prefix;

//	  io_printf (IO_BUF, "mc packet 32 key: %08x, payload: %08x\n", key, payload);

	  if ( (!check) || (check && ((key & mask) == key_space)))
	  {
//		io_printf (IO_BUF, "mc packet 32 key: %08x, payload: %08x\n", key, payload);
		spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
	  }
	  else
		incorrect_keys++;
	}
  }
}

void sdp_packet_callback(uint mailbox, uint port)
{
  use(port);

//  io_printf (IO_BUF, "====================================\n");

  sdp_msg_t *msg = (sdp_msg_t *) mailbox;
  uint16_t *data_hdr = (uint16_t *) &(msg -> cmd_rc);
  uint16_t data_hdr_value = data_hdr[0];
  void *event_pointer = (void *) (data_hdr + 1);

/*
  io_printf (IO_BUF, "data_hdr: %08x\n", (uint32_t) data_hdr);
  io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);

  uint32_t len = msg -> length + 8;
  uint8_t *ptr = (uint8_t *) msg;

  io_printf (IO_BUF, "packet lenght: %d\n", len);
  for (uint32_t i = 0; i < len; i++)
  {
	io_printf (IO_BUF, " %02x", ptr[i]);
  }
  io_printf (IO_BUF, "\n");
*/

  bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
  bool pkt_format = (bool) (data_hdr_value >> 14 & 0x1);
  bool pkt_payload_prefix_apply = (bool) (data_hdr_value >> 13 & 0x1);
  bool pkt_timestamp = (bool) (data_hdr_value >> 12 & 0x1);
  uint8_t pkt_type = (uint8_t) (data_hdr_value >> 10 & 0x3);
  uint8_t pkt_len = (uint8_t) (data_hdr_value & 0xFF);
  bool payload_on = (bool) (pkt_type & 0x1);
  uint32_t pkt_key_prefix = prefix;
  uint32_t pkt_payload_prefix = 0;

/*
  io_printf (IO_BUF, "data_hdr_value: %04x\n", data_hdr_value);
  io_printf (IO_BUF, "pkt_apply_prefix: %d\n", pkt_apply_prefix);
  io_printf (IO_BUF, "pkt_format: %d\n", pkt_format);
  io_printf (IO_BUF, "pkt_payload_prefix: %d\n", pkt_payload_prefix_apply);
  io_printf (IO_BUF, "pkt_timestamp: %d\n", pkt_timestamp);
  io_printf (IO_BUF, "pkt_type: %d\n", pkt_type);
  io_printf (IO_BUF, "pkt_len: %d\n", pkt_len);
  io_printf (IO_BUF, "payload_on: %d\n", payload_on);
*/

  if (pkt_apply_prefix)
  {
	uint16_t *key_prefix_ptr = (uint16_t *) event_pointer;
	event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

	pkt_key_prefix = (uint32_t) key_prefix_ptr[0];

	if (pkt_format) pkt_key_prefix <<= 16;

/*
	io_printf (IO_BUF, "key_prefix_ptr: %08x\n", (uint32_t) key_prefix_ptr);
	io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);
	io_printf (IO_BUF, "pkt_key_prefix: %08x\n", pkt_key_prefix);
*/
  }
  else if (!pkt_apply_prefix && apply_prefix)
  {
	if (key_left_shift == 0)
	  pkt_format = 1;
	else
	  pkt_format = 0;
  }

  if (pkt_payload_prefix_apply)
  {
	if (!(pkt_type & 0x2)) //16 bit type packet
	{
	  uint16_t *payload_prefix_ptr = (uint16_t *) event_pointer;
	  event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

//	  io_printf (IO_BUF, "payload_prefix_ptr: %08x\n", (uint32_t) payload_prefix_ptr);

	  pkt_payload_prefix = (uint32_t) payload_prefix_ptr[0];
	}
	else //32 bit type packet
	{
	  uint16_t *payload_prefix_ptr = (uint16_t *) event_pointer;
	  event_pointer = (void*) (((uint16_t *) event_pointer) + 2);

//	  io_printf (IO_BUF, "payload_prefix_ptr: %08x\n", (uint32_t) payload_prefix_ptr);

	  uint32_t temp1 = payload_prefix_ptr[0];
	  uint32_t temp2 = payload_prefix_ptr[1];
	  pkt_payload_prefix = temp2 << 16 | temp1;
	}

/*
	io_printf (IO_BUF, "event_pointer: %08x\n", (uint32_t) event_pointer);
	io_printf (IO_BUF, "pkt_key_prefix: %08x\n", pkt_key_prefix);
*/
  }

  if (pkt_type <= 1)
	process_16_bit_packets (event_pointer, pkt_format, pkt_len, pkt_key_prefix, pkt_payload_prefix, payload_on, pkt_payload_prefix_apply);
  else
	process_32_bit_packets (event_pointer, pkt_len, pkt_key_prefix, pkt_payload_prefix, payload_on, pkt_payload_prefix_apply);


  //free the message to stop overload
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
  key_left_shift = region_address[2];
  check = region_address[3];
  key_space = region_address[4];
  mask = region_address[5];

  incorrect_keys = 0;

/*
  io_printf (IO_BUF, "apply_prefix: %d\n", apply_prefix);
  io_printf (IO_BUF, "prefix: %d\n", prefix);
  io_printf (IO_BUF, "key_left_shift: %d\n", key_left_shift);
  io_printf (IO_BUF, "check: %d\n", check);
  io_printf (IO_BUF, "key_space: %08x\n", key_space);
  io_printf (IO_BUF, "mask: %08x\n", mask);
*/

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

/*
  // Configure lead app-specific stuff
  if(leadAp)
  {
    system_lead_app_configured();
  }
*/

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
