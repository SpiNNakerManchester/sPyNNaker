#include "../common/common-impl.h"

// Globals
static sdp_msg_t g_spike_message;
static uint16_t *sdp_msg_aer_header;
static void* sdp_msg_aer_data;
static uint32_t time;
static uint32_t packets_sent;
static uint32_t spike_count;

static uint32_t apply_prefix;
static uint32_t prefix;
static uint32_t prefix_type;
static uint32_t key_right_shift;
static uint32_t payload_timestamp;
static uint32_t sdp_tag;
static uint32_t packets_per_timestamp;

static uint32_t payload_apply_prefix;
static uint32_t payload_prefix;
static uint32_t payload_right_shift;

void flush_spikes (void)
{
  // insert appropriate header

  // Send the spike message
  if(spike_count > 0)
  {
    spin1_send_sdp_msg(&g_spike_message, 1);
  }

  //reset packet content
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


  // Cast message data to spikes
  spike_t *data = (spike_t*)g_spike_message.data;

  // If there's still space in the message payload and more incoming spikes
  spike_t s;
  while (g_spike_message.length < SDP_BUF_SIZE && next_spike (& s))
  {
    // Add spike to buffer
    data[g_spike_message.arg2++] = s;

    // Add size of spike to message length
    g_spike_message.length += sizeof(spike_t);
  }

  // Add on size of header to message length
  g_spike_message.length += (sizeof(sdp_hdr_t) + sizeof(cmd_hdr_t));
}

void incoming_spike_callback (uint key, uint payload)
{
#ifdef DEBUG
  log_info("Received spike %x", key);
#endif // DEBUG

#ifdef SPIKE_DEBUG
  io_printf(IO_BUF, "Received spike %x at %d\n", key, time);
  io_printf(IO_STD, "Received spike %x at %d\n", key, time);
#endif // SPIKE_DEBUG

  // process the received spike
}

bool multicast_source_data_filled(address_t base_address) {
  address_t region_address = region_start(1, base_address);

  apply_prefix = region_address[0];			// P bit
  prefix = region_address[1];				// Prefix data
  apply_prefix = region_address[2];			// Type bits
  prefix_type = region_address[3];			// F bit (for the receiver)
  key_right_shift = region_address[4];		// Right packet shift (for the sender)
  payload_timestamp = region_address[5];	// T bit
  payload_apply_prefix = region_address[6];	// D bit
  payload_prefix = region_address[7];		// payload prefix data (for the receiver)
  payload_right_shift = region_address[8];	// Right payload shift (for the sender)
  sdp_tag = region_address[9];
  packets_per_timestamp = region_address[10];

#ifdef DEBUG
  log_info("apply_prefix: %d", apply_prefix);
  log_info("prefix: %08x", prefix);
  log_info("apply_prefix: %d", apply_prefix);
  log_info("prefix_type: %d", prefix_type);
  log_info("key_right_shift: %d", key_right_shift);
  log_info("payload_timestamp: %d", payload_timestamp);
  log_info("payload_apply_prefix: %d", payload_apply_prefix);
  log_info("payload_prefix: %08x", payload_prefix);
  log_info("payload_right_shift: %d", payload_right_shift);
  log_info("sdp_tag: %d", sdp_tag);
  log_info("packets_per_timestamp: %d", packets_per_timestamp);
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

void configure_sdp_msg (void)
{
  // initialize SDP header
  g_spike_message.tag = sdp_tag; // Arbitrary tag
  g_spike_message.flags = 0x07; // No reply required

  g_spike_message.dest_addr = 0; // Chip 0,0
  g_spike_message.dest_port = PORT_ETH; // Dump through Ethernet

  g_spike_message.srce_addr = spin1_get_chip_id();
  g_spike_message.srce_port = (3 << PORT_SHIFT) | spin1_get_core_id(); // Monitoring port

  // initialize AER header
  sdp_msg_aer_header = (void *) &g_spike_message.cmd_rc; // pointer to write data

  // pointers for AER packet header, prefix(es) and data
  sdp_msg_aer_data = (void *) &g_spike_message.cmd_rc; // pointer to write data
  sdp_msg_aer_data = (void *) &g_spike_message.cmd_rc; // pointer to write data

  packets_sent = 0;
  spike_count = 0;
}

// Entry point
void c_main (void)
{
  // Configure system
  system_load_dtcm();

  // Configure SDP message
  configure_sdp_msg();

  // Set timer_callback
  spin1_set_timer_tick(timer_period);

  // Register callbacks
  spin1_callback_on (MC_PACKET_RECEIVED, incoming_spike_callback, -1);
  spin1_callback_on (TIMER_TICK,         timer_callback,           2);

  log_info("Starting");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();

  uint spike_buffer_overflows = buffer_overflows();

  if (spike_buffer_overflows > 0) {
	io_printf(IO_STD, "\tWarning - %d spike buffers overflowed\n",
			  spike_buffer_overflows);
  }
}
