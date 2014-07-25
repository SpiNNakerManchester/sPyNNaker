/*
 * spikes.c
 *
 *
 *  SUMMARY
 *    Incoming spike handling for SpiNNaker neural modelling
 *
 *    The essential feature of the buffer used in this impementation is that it
 *    requires no critical-section interlocking --- PROVIDED THERE ARE ONLY TWO
 *    PROCESSES: a producer/consumer pair. If this is changed, then a more
 *    intricate implementation will probably be required, involving the use
 *    of enable/disable interrupts.
 *
 *  AUTHOR
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
 *    
 *
 *  CREATION DATE
 *    10 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 10 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "common-impl.h"

#ifdef DEBUG
#include "spin-print.h"
#endif /*DEBUG*/

static spike_t*   buffer;
static uint buffer_size;

static index_t   output;
static index_t   input;
static counter_t overflows;
static counter_t underflows;

// unallocated
//
// Returns the number of buffer slots currently unallocated

static inline counter_t unallocated (void)
{ return ((input - output) % buffer_size); }

// allocated
//
// Returns the number of buffer slots currently allocated

static inline counter_t allocated (void)
{ return ((output - input - 1) % buffer_size); }

uint32_t n_spikes_in_buffer(void)
{
  return allocated();
}

// The following two functions are used to determine whether a
// buffer can have an element extracted/inserted respectively.

static inline bool non_empty (void)  { return (allocated   () > 0); }
static inline bool non_full (void)   { return (unallocated () > 0); }

// initialize_spike_buffer
//
// This function initializes the input spike buffer.
// It configures:
//    buffer:     the buffer to hold the spikes (initialized with size spaces)
//    input:      index for next spike inserted into buffer
//    output:     index for next spike extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.

void initialize_spike_buffer (uint size)
{
  buffer = (spike_t *) sark_alloc(1, size * sizeof(spike_t));
  buffer_size = size;
  input      = size - 1;
  output     = 0;
  overflows  = 0;
  underflows = 0;
}

#define peek_next(a) ((a - 1) % buffer_size)

#define next(a) do {(a) = peek_next(a);} while (false)

bool add_spike (spike_t e)
{
  bool success = non_full();

  if (success) {
    buffer [input] = e;
    next (input);
  }
  else
    overflows++;

  return (success);
}

bool next_spike (spike_t* e)
{
  bool success = non_empty();

  if (success) {
    next (output);
    *e = buffer [output];
  }
  else
    underflows++;

  return (success);
}

bool get_next_spike_if_equals(spike_t s)
{
  if (non_empty()) 
  {
    uint peek_output = peek_next(output);
    if (buffer [peek_output] == s) 
    {
      output = peek_output;
      return true;
    }
  }
  return false;
}

// The following two functions are used to access the locally declared
// variables.

counter_t buffer_overflows  (void) { return (overflows);  }
counter_t buffer_underflows (void) { return (underflows); }

#ifdef DEBUG
void print_buffer (void)
{
  counter_t n = allocated();
  index_t   a;

  printf ("buffer: input = %3u, output = %3u elements = %3u\n",
	  input, output, n);
  printf ("------------------------------------------------\n");
  
  for ( ; n > 0; n--) {
    a = (input + n) % IN_SPIKE_SIZE;
    printf ("  %3u: %08x\n", a, buffer [a]);
  }
 
  printf ("------------------------------------------------\n");
}
#endif /*DEBUG*/
