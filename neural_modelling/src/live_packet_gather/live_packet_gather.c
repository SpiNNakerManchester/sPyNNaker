#include "../common/common-impl.h"
#include <sark.h>

// Globals
static sdp_msg_t g_spike_message;
static uint16_t *sdp_msg_aer_header;
static uint16_t *sdp_msg_aer_key_prefix;
static void *sdp_msg_aer_payload_prefix;
static void *sdp_msg_aer_data;
static uint32_t time;
static uint32_t packets_sent;
static uint32_t buffer_index;
static uint16_t temp_header;
static uint8_t spike_size;
static uint8_t header_len;
static bool terminate;

static uint32_t apply_prefix;			// P bit
static uint32_t prefix;					// Prefix data
static uint32_t packet_type;			// Type bits
static uint32_t prefix_type;			// F bit (for the receiver)
static uint32_t key_right_shift;		// Right payload shift (for the sender)
static uint32_t payload_timestamp;		// T bit
static uint32_t payload_apply_prefix;	// D bit
static uint32_t payload_prefix;			// Payload prefix data (for the receiver)
static uint32_t payload_right_shift;	// Right payload shift (for the sender)
static uint32_t sdp_tag;
static uint32_t packets_per_timestamp;

void flush_spikes (void)
{
  // Send the spike message only if there is data
  if(buffer_index > 0)
  {
	uint8_t spike_count;
	uint16_t bytes_to_clear = 0;

	if ((packets_per_timestamp == 0) || (packets_sent < packets_per_timestamp))
	{
	  //check for packet payload
	  if (packet_type & 0x1) // has payload?
		spike_count = buffer_index >> 1;
	  else
		spike_count = buffer_index;

	  // insert appropriate header
	  sdp_msg_aer_header[0] = 0;
	  sdp_msg_aer_header[0] |= temp_header;
	  sdp_msg_aer_header[0] |= (spike_count & 0xff);

	  g_spike_message.length = sizeof (sdp_hdr_t) + header_len + spike_count * spike_size;

	  io_printf(IO_BUF, "===========Packet============\n");
	  uint8_t *print_ptr = (uint8_t *) &g_spike_message;
	  for (uint8_t i = 0; i < g_spike_message.length + 8; i++)
		io_printf(IO_BUF, "%02x ", print_ptr[i]);
	  io_printf(IO_BUF, "\n");

	  if (payload_apply_prefix && payload_timestamp)
	  {
		uint16_t *temp = (uint16_t *) sdp_msg_aer_payload_prefix;
		if (!(packet_type && 0x2)) //16 bit prefix
		{
		  temp[0] = (time & 0xFFFF);
		}
		else
		{
		  temp[0] = (time & 0xFFFF);
		  temp[1] = ((time >> 16) & 0xFFFF);
		}
	  }

	  io_printf(IO_BUF, "===========Packet============\n");
	  print_ptr = (uint8_t *) sdp_msg_aer_data;
	  for (uint8_t i = 0; i < buffer_index * spike_size; i++)
		io_printf(IO_BUF, "%02x ", print_ptr[i]);
	  io_printf(IO_BUF, "\n");

	  spin1_send_sdp_msg(&g_spike_message, 1);
	  packets_sent ++;
	}

	//reset packet content
	bytes_to_clear = buffer_index * spike_size;
	uint16_t *temp = (uint16_t *) sdp_msg_aer_data;
	for (uint8_t i = 0; i < (bytes_to_clear >> 2); i++)
	  temp[i] = 0;
  }

  //reset counter
  buffer_index = 0;
}

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);

  // flush the spike message and sent it over the ethernet
  flush_spikes();

  // increase time variable to keep track of current timestep
  time++;
  log_info("Timer tick %u", time);

  // check if the simulation has run to completion
  if (simulation_ticks != UINT32_MAX && time >= simulation_ticks + timer_period)
  {
    log_info("Simulation complete.\n");

    spin1_exit(0);
  }
}

void flush_spikes_if_full (void)
{
  uint8_t spike_count;

  if (packet_type & 0x1) //payload
	spike_count = buffer_index >> 1;
  else
	spike_count = buffer_index;

  if ((spike_count + 1) * spike_size > 256)
	flush_spikes();
}

// callback for mc packet without payload
void incoming_spike_callback (uint key, uint payload)
{
  uint16_t *buf_pointer = (uint16_t *) sdp_msg_aer_data;

  use(payload);

#ifdef DEBUG
  log_info("Received spike %x", key);
#endif // DEBUG

#ifdef SPIKE_DEBUG
  io_printf(IO_BUF, "Received spike %x at %d\n", key, time);
  io_printf(IO_STD, "Received spike %x at %d\n", key, time);
#endif // SPIKE_DEBUG

  // process the received spike
  if (!(packet_type & 0x2)) //16 bit packet
  {
	buf_pointer[buffer_index]  = (key >> key_right_shift) & 0xFFFF;
	buffer_index ++;
	
	if ((packet_type & 0x1) && (!payload_timestamp)) //if there is a payload to be added
	{
	  buf_pointer[buffer_index] = 0;
	  buffer_index ++;
	}
	else if((packet_type & 0x1) && payload_timestamp)
	{
	  buf_pointer[buffer_index] = (time & 0xFFFF);
	  buffer_index ++;
	}
  }
  else //32 bit packet
  {
	uint16_t spike_index = buffer_index << 1;

	buf_pointer[spike_index] = (key & 0xFFFF);
	buf_pointer[spike_index + 1] = ((key >> 16) & 0xFFFF);
	buffer_index ++;

	if ((packet_type & 0x1) && (!payload_timestamp)) //if there is a payload to be added
	{
	  spike_index = buffer_index << 1;
	  buf_pointer[spike_index] = 0;
	  buf_pointer[spike_index + 1] = 0;
	  buffer_index ++;
	}
	else if((packet_type & 0x1) && payload_timestamp)
	{
	  spike_index = buffer_index << 1;
	  buf_pointer[spike_index] = (time & 0xFFFF);
	  buf_pointer[spike_index + 1] = ((time >> 16) & 0xFFFF);
	  buffer_index ++;
	}
  }

  // send packet if enough data is stored
  flush_spikes_if_full();
}

// callback for mc packet with payload
void incoming_spike_payload_callback (uint key, uint payload)
{
  uint16_t *buf_pointer = (uint16_t *) sdp_msg_aer_data;

#ifdef DEBUG
  log_info("Received spike %x", key);
#endif // DEBUG

#ifdef SPIKE_DEBUG
  io_printf(IO_BUF, "Received spike %x at %d\n", key, time);
  io_printf(IO_STD, "Received spike %x at %d\n", key, time);
#endif // SPIKE_DEBUG

  // process the received spike
  if (!(packet_type & 0x2)) //16 bit packet
  {
	buf_pointer[buffer_index]  = (key >> key_right_shift) & 0xFFFF;
	buffer_index ++;
	
	if ((packet_type & 0x1) && (!payload_timestamp)) //if there is a payload to be added
	{
	  buf_pointer[buffer_index] = (payload >> payload_right_shift) & 0xFFFF;
	  buffer_index ++;
	}
	else if((packet_type & 0x1) && payload_timestamp)
	{
	  buf_pointer[buffer_index] = (time & 0xFFFF);
	  buffer_index ++;
	}
  }
  else //32 bit packet
  {
	uint16_t spike_index = buffer_index << 1;

	buf_pointer[spike_index] = (key & 0xFFFF);
	buf_pointer[spike_index + 1] = ((key >> 16) & 0xFFFF);
	buffer_index ++;

	if ((packet_type & 0x1) && (!payload_timestamp)) //if there is a payload to be added
	{
	  spike_index = buffer_index << 1;
	  buf_pointer[spike_index] = (payload & 0xFFFF);
	  buf_pointer[spike_index + 1] = ((payload >> 16) & 0xFFFF);
	  buffer_index ++;
	}
	else if((packet_type & 0x1) && payload_timestamp)
	{
	  spike_index = buffer_index << 1;
	  buf_pointer[spike_index] = (time & 0xFFFF);
	  buf_pointer[spike_index + 1] = ((time >> 16) & 0xFFFF);
	  buffer_index ++;
	}
  }

  // send packet if enough data is stored
  flush_spikes_if_full();
}

bool multicast_source_data_filled(address_t base_address) {
  address_t region_address = region_start(1, base_address);

  apply_prefix = region_address[0];			// P bit
  prefix = region_address[1];				// Prefix data
  prefix_type = region_address[2];			// F bit (for the receiver)
  packet_type = region_address[3];			// Type bits
  key_right_shift = region_address[4];		// Right packet shift (for the sender)
  payload_timestamp = region_address[5];	// T bit
  payload_apply_prefix = region_address[6];	// D bit
  payload_prefix = region_address[7];		// Payload prefix data (for the receiver)
  payload_right_shift = region_address[8];	// Right payload shift (for the sender)
  sdp_tag = region_address[9];
  packets_per_timestamp = region_address[10];

#ifdef DEBUG
  io_printf(IO_BUF, "apply_prefix: %d\n", apply_prefix);
  io_printf(IO_BUF, "prefix: %08x\n", prefix);
  io_printf(IO_BUF, "prefix_type: %d\n", prefix_type);
  io_printf(IO_BUF, "packet_type: %d\n", packet_type);
  io_printf(IO_BUF, "key_right_shift: %d\n", key_right_shift);
  io_printf(IO_BUF, "payload_timestamp: %d\n", payload_timestamp);
  io_printf(IO_BUF, "payload_apply_prefix: %d\n", payload_apply_prefix);
  io_printf(IO_BUF, "payload_prefix: %08x\n", payload_prefix);
  io_printf(IO_BUF, "payload_right_shift: %d\n", payload_right_shift);
  io_printf(IO_BUF, "sdp_tag: %d\n", sdp_tag);
  io_printf(IO_BUF, "packets_per_timestamp: %d\n", packets_per_timestamp);
#endif

  return (true);
}

bool system_load_dtcm(void) {

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  uint32_t version;
  uint32_t flags = 0;
  if(!system_header_filled (address, &version, flags))
	return (false);

  system_load_params(region_start(0, address));

  if (!multicast_source_data_filled(address))
	return (false);

  return (true);
}

bool configure_sdp_msg (void)
{
//  io_printf(IO_BUF, "configure_sdp_msg\n");

  void *temp_ptr;

  temp_header = 0;
  spike_size = 0;

  // initialize SDP header
  g_spike_message.tag = sdp_tag; // Arbitrary tag
  g_spike_message.flags = 0x07; // No reply required

  g_spike_message.dest_addr = 0; // Chip 0,0
  g_spike_message.dest_port = PORT_ETH; // Dump through Ethernet

  g_spike_message.srce_addr = spin1_get_chip_id();
  g_spike_message.srce_port = (3 << PORT_SHIFT) | spin1_get_core_id(); // Monitoring port

  // check incompatible options
  if (payload_timestamp && payload_apply_prefix && (packet_type & 0x1))
  {
	io_printf(IO_BUF, "Error: Timestamp can either be included as payload prefix or as payload to each key, not both\n");
	return false;
  }
  if (payload_timestamp && !payload_apply_prefix && !(packet_type & 0x1))
  {
	io_printf(IO_BUF, "Error: Timestamp can either be included as payload prefix or as payload to each key, but current configuration does not specify either of these\n");
	return false;
  }

  // initialize AER header
  sdp_msg_aer_header = &g_spike_message.cmd_rc; // pointer to data space

  temp_header |= (apply_prefix << 15);
  temp_header |= (prefix_type << 14);
  temp_header |= (payload_apply_prefix << 13);
  temp_header |= (payload_timestamp << 12);
  temp_header |= (packet_type << 10);

  header_len = 2;
  temp_ptr = (void *) sdp_msg_aer_header[1];

  // pointers for AER packet header, prefix(es) and data
  if (apply_prefix)
  {
	sdp_msg_aer_key_prefix = (sdp_msg_aer_header+1); // pointer to key prefix
	temp_ptr = (void *) (sdp_msg_aer_header+2);
	sdp_msg_aer_key_prefix[0] = (uint16_t) prefix;
	header_len += 2;
  }
  else
  {
	sdp_msg_aer_key_prefix = NULL;
	temp_ptr = (void *) (sdp_msg_aer_header+1);
  }

  if (payload_apply_prefix)
  {
	sdp_msg_aer_payload_prefix = temp_ptr;
	uint16_t *a = (uint16_t *) sdp_msg_aer_payload_prefix;
	
//	io_printf(IO_BUF, "temp_ptr: %08x\n", (uint32_t) temp_ptr);
//	io_printf(IO_BUF, "a: %08x\n", (uint32_t) a);
	sdp_msg_aer_payload_prefix = temp_ptr; // pointer to payload prefix
	if (!(packet_type & 0x2)) //16 bit payload prefix
	{
	  temp_ptr = (void *) (a + 1);
	  header_len += 2;
	  if (!payload_timestamp) // add payload prefix as required - not a timestamp
	  {
		a[0] = payload_prefix;
	  }
//	  io_printf(IO_BUF, "16 bit - temp_ptr: %08x\n", (uint32_t) temp_ptr);
	}
	else //32 bit payload prefix
	{
	  temp_ptr = (void *) (a + 2);
	  header_len += 4;
	  if (!payload_timestamp) // add payload prefix as required - not a timestamp
	  {
		a[0] = (payload_prefix & 0xFFFF);
		a[1] = ((payload_prefix >> 16) & 0xFFFF);
	  }
//	  io_printf(IO_BUF, "32 bit - temp_ptr: %08x\n", (uint32_t) temp_ptr);
	}
  }
  else
  {
	sdp_msg_aer_payload_prefix = NULL;
  }

  sdp_msg_aer_data = (void *) temp_ptr; // pointer to write data

  switch (packet_type)
  {
	case 0:
	  spike_size = 2;
	  break;
	case 1:
	  spike_size = 4;
	  break;
	case 2:
	  spike_size = 4;
	  break;
	case 3:
	  spike_size = 8;
	  break;
	default:
	  io_printf(IO_BUF, "error: unknown packet type: %d\n", packet_type);
	  exit(1);
	  break;
  }

//  io_printf(IO_BUF, "sdp_msg_aer_header: %08x\n", (uint32_t) sdp_msg_aer_header);
//  io_printf(IO_BUF, "sdp_msg_aer_key_prefix: %08x\n", (uint32_t) sdp_msg_aer_key_prefix);
//  io_printf(IO_BUF, "sdp_msg_aer_payload_prefix: %08x\n", (uint32_t) sdp_msg_aer_payload_prefix);
//  io_printf(IO_BUF, "sdp_msg_aer_data: %08x\n", (uint32_t) sdp_msg_aer_data);

  packets_sent = 0;
  buffer_index = 0;
  
  return true;
}

// Entry point
void c_main (void)
{
  bool ans;

  // Configure system
  ans = system_load_dtcm();
  if (!ans) return;

  // Configure SDP message
  ans = configure_sdp_msg();
  if (!ans) return;

  // Set timer_callback
  spin1_set_timer_tick(timer_period);

  // Register callbacks
  spin1_callback_on (MC_PACKET_RECEIVED,   incoming_spike_callback,         -1);
  spin1_callback_on (MCPL_PACKET_RECEIVED, incoming_spike_payload_callback, -1);
  spin1_callback_on (TIMER_TICK,           timer_callback,                   2);

  io_printf(IO_BUF, "Starting\n");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();

  uint spike_buffer_overflows = buffer_overflows();

  if (spike_buffer_overflows > 0) {
	io_printf(IO_STD, "\tWarning - %d spike buffers overflowed\n",
			  spike_buffer_overflows);
  }
}
