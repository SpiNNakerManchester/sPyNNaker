#include "../common/common-impl.h"

// Globals
static sdp_msg_t g_spike_message;
static uint32_t time;

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;

  log_info("Timer tick %u", time);
  
  if (simulation_ticks != UINT32_MAX && time >= simulation_ticks + timer_period)
  {
    log_info("Simulation complete.\n");
    
    spin1_exit(0);
  }
  
  // Reset SDP message arguments
  g_spike_message.length = 0;
  g_spike_message.arg1 = time;
  g_spike_message.arg2 = 0;
  g_spike_message.arg3 = 1000;
  
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
  
  // Send the spike message
  // **NOTE** 1ms timeout
  if(g_spike_message.arg2 > 0)
  {
    spin1_send_sdp_msg(&g_spike_message, 1);
  }
}

void incoming_spike_callback (uint key, uint payload)
{
  use(payload);
  
#ifdef DEBUG
  log_info("Received spike %x", key);
#endif // DEBUG

#ifdef SPIKE_DEBUG
  io_printf(IO_BUF, "Received spike %x at %d\n", key, time);
  io_printf(IO_STD, "Received spike %x at %d\n", key, time);
#endif // SPIKE_DEBUG

  // If there was space to add spike to incoming spike queue
  add_spike(key);
  
}

bool system_load_dtcm(void) {

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  uint32_t version;
  uint32_t flags   = 0;
  if(!system_header_filled (address, &version, flags))
  {
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
  
  // Initialize the incoming spike buffer
  initialize_spike_buffer (8192);
  
  // Configure SDP message
  g_spike_message.tag = 1; // Arbitrary tag
  g_spike_message.flags = 0x07; // No reply required
  
  g_spike_message.dest_addr = 0; // Chip 0,0
  g_spike_message.dest_port = PORT_ETH; // Dump through Ethernet
  
  g_spike_message.srce_addr = spin1_get_chip_id();
  g_spike_message.srce_port = (3 << PORT_SHIFT) | spin1_get_core_id(); // Monitoring port
  
  g_spike_message.cmd_rc = 64; // Monitoring channel
  g_spike_message.length = 0;
  
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
