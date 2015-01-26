/*
 * A harness for connecting the neural application coded into
 * the spin1_api framework.
 *
 * Dave Lester
 *
 */

#include "spin-neuron-impl.h"
#include "synapses_impl.h"

// Globals
static uint32_t  dma_index;                                  //              4
static uint32_t  dma_busy;                                   //              4
static uint32_t  dma_buffer1 [DMA_BUFFER_SIZE + 2];          //           1038 bytes
static uint32_t  dma_buffer2 [DMA_BUFFER_SIZE + 2];          //           1038 bytes
static uint32_t* dma_buffer[2] = {dma_buffer1, dma_buffer2}; //              8

static inline uint32_t* current_dma_buffer() { return (dma_buffer[dma_index]);}
static inline uint32_t* next_dma_buffer()    { return (dma_buffer[dma_index ^ 1]); }
static inline void      swap_dma_buffers()   { dma_index ^= 1; }

// Globals
#ifdef SYNAPSE_BENCHMARK
  uint32_t  num_fixed_pre_synaptic_events = 0;
  uint32_t  num_plastic_pre_synaptic_events = 0;
#endif  // SYNAPSE_BENCHMARK

// DMA tags
#define DMA_TAG_READ_SYNAPTIC_ROW 0
#define DMA_TAG_WRITE_PLASTIC_REGION 1

void initialise_dma_buffers()
{
  // Reset dma chain settings
  dma_index = 0;
  dma_busy  = FALSE;
}


void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);

  time++;

  log_info("Timer tick %u", time);

  // if a fixed number of simulation ticks are specified and these have passed
  if (simulation_ticks != UINT32_MAX && time >= simulation_ticks)
  {
    log_info("Simulation complete.\n");

#ifdef SYNAPSE_BENCHMARK
    io_printf(IO_BUF, "Simulation complete - %u/%u fixed/plastic pre-synaptic events.\n", num_fixed_pre_synaptic_events, num_plastic_pre_synaptic_events);
#endif  // SYNAPSE_BENCHMARK

    print_saturation_count();

    // Finalise any recordings that are in progress, writing back the final amounts of samples recorded to SDRAM
    recording_finalise();
    spin1_exit(0);

    uint spike_buffer_overflows = buffer_overflows();
    if (spike_buffer_overflows > 0)
    {
      io_printf(IO_STD, "\tWarning - %d spike buffers overflowed\n", spike_buffer_overflows);
    }
    return;
  }

  // **NOTE** may need critical section to handle interaction with process_synaptic_row
  uint sr = spin1_irq_disable();
  ring_buffer_transfer();
  spin1_mode_restore(sr);
  //print_currents ();

  // Tick neural simulation
  for (index_t n = 0; n < num_neurons; n++)
  {
    neuron (n);
  }


  //print_neurons ();
  // Record output spikes if required
  record_out_spikes();

  if (nonempty_out_spikes ())
  {
    print_out_spikes ();
    for (index_t i = 0; i < num_neurons; i++)
    {
      if (out_spike_test (i))
      {
#ifdef SPIKE_DEBUG
        io_printf(IO_BUF, "Sending spike packet %x at %d\n", key | i, time);
#endif // SPIKE_DEBUG
        while (!spin1_send_mc_packet(key | i, NULL, NO_PAYLOAD))
        {
            spin1_delay_us(1);
        }
      }
    }
    reset_out_spikes ();
  }

  /*for (n = 0; n < num_neurons; n++) {
    iaf_psc_exp_dynamics(n);
  }*/
}

void set_up_and_request_synaptic_dma_read()
{
  // If there's more incoming spikes
  spike_t s;
  uint32_t setup_done = FALSE;
  while (!setup_done && next_spike (& s))
  {
#ifdef SPIKE_DEBUG
    io_printf(IO_BUF, "Checking for row for spike %x\n", s);
#endif
    // Decode spike to get address of destination synaptic row
    address_t address;
    size_t size_bytes;
    if(synaptic_row(&address, &size_bytes, s) != 0)
    {
      // Write the SDRAM address and originating spike to the beginning of dma buffer
      current_dma_buffer()[0] = (uint32_t)address;
      current_dma_buffer()[1] = s;
      setup_done = TRUE;
//#ifdef DMA_DEBUG
//      io_printf(IO_BUF, "Processing spike %x via DMA\n", s);
//#endif

      // Start a DMA transfer to fetch this synaptic row into current buffer
      spin1_dma_transfer(DMA_TAG_READ_SYNAPTIC_ROW, address, &current_dma_buffer()[2], DMA_READ, size_bytes);

      // Flip DMA buffers
      swap_dma_buffers();
    }
  }

  // If the setup was not done, and there are no more spikes,
  // stop trying to set up synaptic dmas
  if (!setup_done)
  {
#if defined(SPIKE_DEBUG) || defined(DMA_DEBUG)
    io_printf(IO_BUF, "DMA not busy\n");
#endif // SPIKE_DEBUG || DMA_DEBUG
    log_info("DMA not busy");
    dma_busy = FALSE;
  }
}

void set_up_and_request_synaptic_dma_write()
{
  // Get the number of plastic bytes and the writeback address from the synaptic row
  size_t plastic_region_bytes = plastic_size(next_dma_buffer()) * sizeof(uint32_t);
  address_t writeback_address = plastic_write_back_address(next_dma_buffer());

  log_info("Writing back %u bytes of plastic region to %08x", plastic_region_bytes, writeback_address);

  // Start transfer
  spin1_dma_transfer (DMA_TAG_WRITE_PLASTIC_REGION,
    writeback_address,
    plastic_region(next_dma_buffer()),
    DMA_WRITE,
    plastic_region_bytes);
}

void dma_callback(uint unused, uint tag)
{
  use(unused);

  log_info("DMA transfer complete tag %u", tag);
//#ifdef DMA_DEBUG
//  io_printf(IO_BUF, "DMA transfer complete with tag %u\n", tag);
//#endif

  // If this DMA is the result of a read
  if(tag == DMA_TAG_READ_SYNAPTIC_ROW)
  {
    // **NOTE** may need critical section to handle interaction with ring_buffer_transfer

    // Extract originating spike from start of DMA buffer
    spike_t s = originating_spike(next_dma_buffer());

    // Process synaptic row repeatedly
    bool subsequent_spikes;
    do
    {
      // Are there any more incoming spikes from the same pre-synaptic neuron?
      subsequent_spikes = get_next_spike_if_equals(s);

      // Process synaptic row, writing it back if it's the last time it's going to be processed
      print_synaptic_row(next_dma_buffer());
      process_synaptic_row(next_dma_buffer(), !subsequent_spikes);

    } while (subsequent_spikes);

    // **NOTE** writeback should occur here so DMA is performed BEFORE setting up
    // Next synaptic row read therefore, we need 3 buffers rather than 2
    set_up_and_request_synaptic_dma_read();
  }
  // Otherwise, if it ISN'T the result of a plastic region write
  else if(tag != DMA_TAG_WRITE_PLASTIC_REGION)
  {
    io_printf(IO_BUF, "Invalid tag %d received in DMA\n", tag);
    sentinel("tag (%d)", tag);
  }
}

void incoming_spike_callback (uint key, uint payload)
{
  use(payload);

#if defined(DEBUG) || defined(SPIKE_DEBUG) || defined(DMA_DEBUG)
  io_printf(IO_BUF, "Received spike %x at %d, DMA Busy = %d\n", key, time, dma_busy);
#endif // SPIKE_DEBUG || DMA_DEBUG

  // If there was space to add spike to incoming spike queue
  if(add_spike(key))
  {
    // If we're not already processing synaptic dmas, flag pipeline as busy and trigger a feed event
    if (!dma_busy)
    {
      log_info("Sending user event for new spike");
      if (spin1_trigger_user_event(0, 0))
      {
        dma_busy = TRUE;
      } else {
    	io_printf(IO_BUF, "\t[WARNING] Could not trigger user event\n");
      }
    }
  } else {
    log_info("Could not add spike");
  }

}


void feed_dma_pipeline (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);

#ifdef DMA_DEBUG
  io_printf(IO_BUF, "Preparing to read DMA pipeline\n");
#endif

  set_up_and_request_synaptic_dma_read();

#ifdef DMA_DEBUG
  io_printf(IO_BUF, "Finished DMA pipeline setup");
#endif
}
