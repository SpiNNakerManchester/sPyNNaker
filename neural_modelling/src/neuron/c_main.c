/*
 * c_main.c
 *
 * SUMMARY
 *  This file contains the main function of the application framework, which
 *  the application programmer uses to configure and run applications.
 *
 * AUTHOR
 *    Thomas Sharp - thomas.sharp@cs.man.ac.uk
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *    A header file that can be used as the API for the spin-neuron.a library.
 *    To use the code is compiled with
 *
 *      #include "debug.h"
 *
 *  CREATION DATE
 *    21 July, 2013
 *
 *  HISTORY
 *    DETAILS
 *    Created on       : 27 July 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 */

#include "spin-neuron-impl.h"
#include "models/generic_neuron.h"

//extern neuron_t *neuron_array;
/*
#define PRINT_NEURON( i ) \
  io_printf( IO_STD, "V_th=%k V_r=%k V_rt=%k R=%k V_m=%k I=%k etc=%k Tref=%d reft=%d\n",  \
    neuron_array[i].V_thresh, \
    neuron_array[i].V_reset, \
    neuron_array[i].V_rest, \
    neuron_array[i].R_membrane, \
    neuron_array[i].V_membrane, \
    neuron_array[i].I_offset, \
    neuron_array[i].exp_TC, \
    neuron_array[i].T_refract, \
    neuron_array[i].refract_timer \
  );
*/
// **TODO** move somewhere else!
void initialize_buffers (void)
{
  //log_info("Initializing buffers");

  time = 0;

  reset_ring_buffer ();
  initialize_current_buffer ();
  initialize_spike_buffer (IN_SPIKE_SIZE);
  initialise_plasticity_buffers();
  initialise_dma_buffers();


  //log_info("resetting of buffers completed");
}

void c_main (void)
{

#ifdef SPIN1_API_HARNESS
  // Load DTCM data
  system_load_dtcm();

  initialize_buffers();

  // setup function which needs to be called in main program before any neuron code executes
  // currently minimum 100 microseconds, then in 100 steps...  if not called then defaults to 1ms(=1000us)
  provide_machine_timestep( h );

  // Set timer tick (in microseconds)
  spin1_set_timer_tick (timer_period);

  // Register callbacks
  spin1_callback_on (MC_PACKET_RECEIVED, incoming_spike_callback, -1);
  spin1_callback_on (DMA_TRANSFER_DONE,  dma_callback,             0);
  spin1_callback_on (USER_EVENT,         feed_dma_pipeline,        0);
  spin1_callback_on (TIMER_TICK,         timer_callback,           2);
  //spin1_callback_on (SDP_PACKET_RX,      sdp_packet_callback,      1);

  log_info("Starting");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();
#else
   uint32_t version;

  if (dtcm_filled ((uint32_t*)(0x74000000), & version, 0))
  {
    log_info ("DTCM OK %u", num_neurons );
  }

  initialize_buffers ();

  log_info ("Buffers OK");
/*
  for( index_t i = 0; i < num_neurons; i++ )
  {
    PRINT_NEURON( i );

    //		neuron_array[i].V_membrane = REAL_CONST( 0.0 );
    neuron_array[i].T_refract = 25;

  }
  */
  add_spike (make_key (0, 0, key_p(key)));

  log_info ("add_spike OK");

  harness ();

#endif
}
