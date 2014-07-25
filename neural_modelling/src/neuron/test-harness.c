/*
 * test-harness.c
 * 
 * A deterministic test harness for a single population on a single core.
 *
 * It permits extensive tesing of the core code, and should be used as a key
 * first stage in the regression testing regime.
 *
 */

#include "spin-neuron-impl.h"

extern timer_t time; // The global timer
extern key_t   key;  // The global top 22 bits of the key (constant after configuration)

// process_outgoing_spikes
//
// This function arranges for the transmission of outgoing spikes.
//
// It could be reconfigured later so that we have a longer term record of active and
// inactive neurons (by AND-ing or OR-ing the bitfields). This might be important for
// plasticity and recording purposes.

void  process_outgoing_spikes (void)
{
  index_t i;

  if (nonempty_out_spikes ()) {
    print_out_spikes ();      // prints out the bitfield
    for (i = 0; i < num_neurons; i++)
      if (out_spike_test (i))
	send_spike (key | i); // sends spike
    reset_out_spikes ();      // resets bitfield to be empty
  }

  return;
}

// process_spike
//
// This function processes an incoming spike "e"

static inline void process_spike (key_t e)
{
  address_t address;
  size_t    size_bytes;
  int s;

  s = synaptic_row (&address, &size_bytes, e);
                              // We get the address/size of the synaptic row.
                              // The size is an over-estimate of the actual size
                              //     rounded up to a power of 2.

  log_info("address %08x, size %u bytes, s = %u\n", (uint32_t)address, size_bytes, s);

  print_synaptic_row   (address);
  process_synaptic_row (address);
                              // This function transfers "weight" to the ring_buffer
}

// process_neurons
//
// This function performs neuron calculations

static inline void process_neurons (void)
{
  index_t n;

  for (n = 0; n < num_neurons; n++)
    neuron (n);
}

// harness_tick
//
// This function performs the actions associated with a single
// time step or clock tick;

void harness_tick (void)
{

  time++;                     // Increment the timer.

  spike_t s;

  log_info("Start of tick %u, ...", time);

  ring_buffer_transfer ();    // We tranfer the "front" ring_buffer elements
                              //  to the current_buffers.
  print_currents ();

  while (next_spike (& s))    // while there are still spikes to process..
    process_spike (spike_key (s));
                              // .. we process them.

  print_ring_buffers ();

  process_neurons ();         // We process each neuron in turn.

  print_neurons ();

  process_outgoing_spikes (); // Then we transmit spikes.
}

// harness
//
// Iterate through the required number of ticks. Perhaps make
// this dependent on a value supplied by Simon's PACMAN?

void harness (void)
{
  timer_t t = 26;

  for ( ; t > 0; t--)
    harness_tick();
}

// send_spike
//
// Add an outgoing spike to the _incoming_ spike buffer.

void send_spike (spike_t n)
{
  log_info("Sending spike packet %x", n);

  if (!add_spike (n))
    io_printf (IO_BUF, "spike buffer full\n");
}
