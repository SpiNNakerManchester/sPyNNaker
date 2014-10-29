/*
 * synapses.c
 *
 *
 *  SUMMARY
 *    Synaptic processing
 *
 *    That is:
 *     (1) "synaptic_row"
 *
 *          We caclulate the SDRAM address and an over-estimate
 *          of the size of the synaptic row (for DMA setup); and
 *
 *     (2) "process_synaptic_events"
 *
 *         This uses the information in the synaptic row to
 *         updfate the ring buffer
 *
 *     (3) "ring_buffer_transfer" transfers the 'front' of
 *         the ring buffer to the currents, doing any
 *         necessary shaping.
 *
 *    There are also support functions for:
 *     
 *     (-) printing (if #def'd)
 *     (-) configuration
 *     (-) randomly setting up data structures
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
 *    9 August, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 9 August 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "spin-neuron-impl.h"

#include "synapses_impl.h"

// **NOTE** synapse shaping implementation gets included by compiler

// ring buffers between synapses and neurons.
static ring_entry_t  ring_buffer   [RING_BUFFER_SIZE];

current_t *current;

// synaptic row indexing
static uint16_t  master_population [MASTER_POPULATION_MAX];
static uint32_t* synaptic_row_base;
static uint32_t  row_size_table    [ROW_SIZE_TABLE_MAX];

// 2D array of synapse decays - num synapse types by
synapse_param_t *neuron_synapse_params[SYNAPSE_TYPE_COUNT];

// initialize_current_buffer
//
// This function allocates the current buffer, and sets each element to zero

void initialize_current_buffer (void)
{
  counter_t i;

  current = (current_t*)sark_alloc(CURRENT_BUFFER_SIZE*sizeof(current_t), 1);
  log_info ("address of current %x - Current buffer size %u, ring-buffer size %u", (uint32_t)current, CURRENT_BUFFER_SIZE, RING_BUFFER_SIZE);

  for (i = 0; i < CURRENT_BUFFER_SIZE; i++)
  {
    current[i] = current_0;
  }
}

// Weights are treated as u12.4 fixed point quantities, and
// are considered as currents measured in pA. This means that
// 300 pA is given the value 4800 (=0x12c0).
//
// We now need to convert this value into a 32-bit
// representation of the current.
//
// At the moment we merely take the u12.4 value and
// convert to an s16.15 value; this is a left shift of 11

static inline current_t weight_to_current (weight_t w)
{
  union { int_k_t r; s1615 fx; } x;

  x.r = (int_k_t)(w) << ring_buffer_to_input_left_shift;

  return x.fx;
}

// ring_buffer_transfer
//
// This function transfers the "weights" at the front of the ring buffer
// to the current buffer(s). To do this we do the following:
//
//   (1) Shape the current buffers, by decaying the previous values.
//       This may have the effect of zero-ing the current buffers
//       (propogator of zero, or delta synapses).
//
//   (2) We then add in the weights
//
//   (3) Finally, we zero the ring_buffer elements.
//
// Provided this is carried out at the beginning of a clock tick
// -- _before_ any attempt is made to transfer spikes to the ring buffer --
// we do not need to interlock using critical sections (i.e. interrupt
// enabling/disabling).
//
// In these circustances we can use _all_ ring buffer values for transfers
// i.e. delays in the range 1 - 16 (represented by 1-15 and 0). 

void ring_buffer_transfer (void)
{
  for (uint32_t n = 0; n < num_neurons; n++) 
  {
    // Shape the current according to the included rume
    shape_current(n);
  
    // Loop through all synapse types
    for(uint32_t s = 0; s < SYNAPSE_TYPE_COUNT; s++)
    {
      // Get offset of ring-buffer input for this synapse type
      uint32_t off = offset_ring_buffer (time, s, n);
      
      // Convert ring-buffer entry to current and add on to correct input current for this s
      add_neuron_input(n, s, weight_to_current(ring_buffer [off]));
      
      // Clear ring buffer
      ring_buffer [off] = 0;
    }
  }
}

// Before we process a synapse, we must find the synaptic row
// associated with the spike key held in the incoming spike buffer.

int synaptic_row (address_t* address, size_t* size_bytes, spike_t key)
{
  uint32_t pid = make_pid (key_x (key), key_y (key), key_p (key));
                                              // top 22 bits for population id
  uint32_t nid = key &  KEY_MASK;   // lowest 10 bits
  uint32_t d, s, stride;

  check((pid < MASTER_POPULATION_MAX), "0 <= population_id (%u) < %u", pid,  MASTER_POPULATION_MAX);

  d = (uint32_t)(master_population [pid]);
  s = d & 0x7; // get lowest 3 bits into s;
  d = d >> 3;  // d is now only 13 bits, i.e. 0..8095 .

  //log_info("spike = %08x, pid = %u, s = %u, d = %u, nid = %u",
  //  key, pid, s, d, nid);

  if(s == 0)
  {
    log_info ("spike %u (= %x): population not found in master population table", key, key);
  }
  else
  {
    // Convert row size to bytes
    // **THINK** this is dependant on synaptic row format so could be dependant on implementatin
    uint32_t num_synaptic_words = row_size_table [s];
    *size_bytes = (num_synaptic_words + 3) * sizeof(uint32_t);
    
    stride   = (row_size_table [s] + 3);
    uint32_t neuron_offset   = nid * stride * sizeof (uint32_t);
    
    // **NOTE** 1024 converts from kilobyte offset to byte offset
    uint32_t population_offset = d * 1024;
    
    //log_info("stride = %u, neuron offset = %u, population offset = %u, base = %08x, size = %u", stride, neuron_offset, population_offset, synaptic_row_base, *size_bytes);
    
    *address = (uint32_t*) ((uint32_t)synaptic_row_base + population_offset + neuron_offset);
  }
  
  return (s);
}

// This is the "inner loop" of the neural simulation.
// Every spike event could cause upto 256 different weights to
// be put into the ring buffer.
static inline void process_fixed_synapses (address_t fixed)
{
  register uint32_t *synaptic_words = fixed_weight_controls(fixed);
  register uint32_t fixed_synapse  = num_fixed_synapses(fixed);
  register uint32_t synaptic_word, delay;
  register uint32_t weight;
  register uint32_t offset, index;
  register ring_entry_t *rp = ring_buffer;
  register uint32_t t = time;
  
  for ( ; fixed_synapse > 0; fixed_synapse--) 
  {
    // Get the next 32 bit word from the synaptic_row (should autoincrement pointer in single instruction)
    synaptic_word = *synaptic_words++;

    // Extract components from this word
    delay = sparse_delay(synaptic_word);
    index = sparse_type_index(synaptic_word);
    weight = sparse_weight(synaptic_word);
    
    // Convert into ring buffer offset
    offset = offset_sparse(delay + t, index);
    
    // Add weight to ring-buffer entry
    // **NOTE** Dave suspects that this could be a potential location for overflow
    rp[offset] += weight;         // Add the weight to the current ring_buffer value.
  }
}


void process_synaptic_row (synaptic_row_t row, bool write)
{
  // Get address of non-plastic region from row
  address_t fixed   = fixed_region(row);
  // **TODO** multiple optimised synaptic row formats
  //if (plastic_tag(row) == 0)
  //{
  // If this row has a plastic region
  if(plastic_size(row) > 0)
  {
    // Get region's address
    address_t plastic = plastic_region(row);

    // Process any plastic synapses
    process_plastic_synapses(plastic, fixed, ring_buffer);

    // Perform DMA writeback
    // **NOTE** this isn't great as we're assuming something about 
    // Structure of harness DMA implementation i.e. that row == next_dma_buffer()
    if(write)
    {
      set_up_and_request_synaptic_dma_write();
    }
  }

  // Process any fixed synapses
  // **NOTE** this is done after initiating DMA in an attempt
  // To hide cost of DMA behind this loop to Improve change
  // That DMA controller is ready to read next synaptic row afterwards
  process_fixed_synapses(fixed);
  //}
}

// The following functions are used to read the data provided by PACMAN
// They are called from within the file configuration.c, but need access
// to the static data structures in this file, and are therefore
// defined here.

void reset_ring_buffer (void)
{
  counter_t i;

  for (i = 0; i < RING_BUFFER_SIZE; i++)
  {
    ring_buffer[i] = (ring_entry_t)(0);
  }
}

bool row_size_table_filled (uint32_t* address, uint32_t flags)
{
  counter_t i;
  bool success = true;

  use(flags);

  log_info("row_size_table_filled: starting");

  if (!(vector_copied(& (row_size_table[0]), 8, address, flags)))
    success = false;

  // We should have eight 32 bit words in this region.
  //
  // The results should be 0, 1, 8, 16, 32, 64, 128, 256, in order.

  for (i = 0; i < 8; i++)
  {
    if ((i < 2 && row_size_table[i] != i) || (i >= 2 && row_size_table[i] != (uint32_t)(1 << (i+1))))
    {
      success = false;
    }
  }

  log_info("row_size_table_filled: completed successfully");

  print_row_size_table ();

  return (success);
}

bool master_population_table_filled (uint32_t* address, uint32_t flags)
{
  bool success = true;
  use(flags);

  log_info("master_population_table_filled: starting");

  if (!(half_word_vector_copied (master_population, MASTER_POPULATION_MAX, address, flags)))
    success = false;

  log_info("master_population_table_filled: completed successfully");

  print_master_population ();

  return (success);
}

bool synaptic_data_filled (address_t address, uint32_t flags)
{
  use(flags);

  synaptic_row_base = address;

  log_info("address of base of synatic matrix %08x", (uint32_t)address);
 
  return (true);
}

bool synaptic_current_data_filled (address_t address, uint32_t flags)
{
  use(flags);
  
  log_info("synaptic_current_data_filled: starting");
  
  // Loop through synapse types
  for(index_t s = 0; s < SYNAPSE_TYPE_COUNT; s++)
  {
    log_info("\tCopying %u synapse type %u parameters of size %u", num_neurons, s, sizeof(synapse_param_t));
    
    // Allocate block of memory for this synapse type's pre-calculated per-neuron decay
    neuron_synapse_params[s] = (synapse_param_t*) spin1_malloc(sizeof(synapse_param_t) * num_neurons);
    
    // Check for success
    if(neuron_synapse_params[s] == NULL)
    {
      sentinel("Cannot allocate neuron synapse decay parameters - Out of DTCM");
      return false;
    }
    
    log_info("\tCopying %u bytes to %u", num_neurons * sizeof(synapse_param_t), address + ((num_neurons * s * sizeof(synapse_param_t)) / 4));
    memcpy(neuron_synapse_params[s], address + ((num_neurons * s * sizeof(synapse_param_t)) / 4),
    		num_neurons * sizeof(synapse_param_t));
  }
  
  log_info("synaptic_current_data_filled: completed successfully");
  return true;
}

#ifdef DEBUG

// We are treating weights as u12.4 fixed point format.
// This requires a shift when printing them out.

void print_weight (weight_t w)
{
  if (w != 0) printf ("%12.6k", weight_to_current(w));
  else        printf ("      ");
}

void print_ring_buffers (void)
{
  counter_t d, n, t;
  bool empty;
  
  printf ("Ring Buffer\n");
  printf ("-----------------------------------------------------------------\n");
  for (n = 0; n < (1 << SYNAPSE_INDEX_BITS); n++) 
  {
    for (t = 0; t < SYNAPSE_TYPE_COUNT; t++) 
    {
      const char *type_string = get_synapse_type_char(t);
      empty = true;
      for (d = 0; d < (1 << SYNAPSE_DELAY_BITS); d++)
      {
        empty = empty && (ring_buffer[offset_ring_buffer(d + time, t, n)] == 0);
      }
      if (!empty) 
      {
        printf("%3d(%s):", n, type_string);
        for (d = 0; d < (1 << SYNAPSE_DELAY_BITS); d++) 
        {
          printf(" ");
          print_weight (ring_buffer[offset_ring_buffer(d + time, t, n)]);
        }
        printf ("\n");
      }
    }
  }
  printf ("-----------------------------------------------------------------\n");
}

void print_master_population (void)
{
  uint32_t i,s,mp;

  printf ("master_population\n");
  printf ("------------------------------------------\n");
  for (i = 0; i < MASTER_POPULATION_MAX; i++) 
  {
    mp = (uint32_t)(master_population[i]);
    s  = mp & 0x7;
    if (s != 0)
    {
      printf ("index %d, entry: %4u ( 13 bits = %04x), size = %3u\n",
	      i, mp, mp >> 3, row_size_table [s]);
    }
  }
  printf ("------------------------------------------\n");
}

void print_row_size_table (void)
{
  uint32_t i;

  printf ("row_size_table\n");
  printf ("------------------------------------------\n");
  for (i = 0; i < ROW_SIZE_TABLE_MAX; i++)
  {
    printf ("  index %2u, size = %3u\n", i, row_size_table [i]);
  }
  printf ("------------------------------------------\n");
}

void print_synaptic_rows (uint32_t* rows)
{ 
  use(rows); 
  return; 
}

void print_synaptic_row (synaptic_row_t synaptic_row)
{
  printf ("\nSynaptic row, at address %08x Num plastic words:%u\n", (uint32_t)synaptic_row, plastic_size(synaptic_row));
  if (synaptic_row == NULL) 
  {
    return;
  }
  printf ("----------------------------------------\n");
  // Get details of fixed region
  address_t fixed = fixed_region(synaptic_row);
  address_t fixed_synapses = fixed_weight_controls(fixed);
  size_t num = num_fixed_synapses(fixed);
  printf ("Fixed region %u fixed synapses (%u plastic control words):\n", num, num_plastic_controls(fixed));

  for (uint32_t i = 0; i < num; i++)
  {
    uint32_t x = fixed_synapses[i];

    printf ("%08x [%3d: (w: %5u (=", x, i, sparse_weight(x));
    print_weight (sparse_weight(x));
    printf ("nA) d: %2u, %s, n = %3u)] - {%08x %08x}\n",
      sparse_delay(x),
      get_synapse_type_char(sparse_type(x)),
      sparse_index(x),
      SYNAPSE_DELAY_MASK,
      SYNAPSE_TYPE_INDEX_BITS
    );
  }

  // If there's a plastic region
  if(plastic_size(synaptic_row) > 0)
  {
    printf ("----------------------------------------\n");
    address_t plastic = plastic_region(synaptic_row);
    print_plastic_synapses(plastic, fixed);
  }
  
  printf ("----------------------------------------\n");
}

uint32_t* generate_synfire_chain(uint32_t* start, uint32_t delay, uint32_t p)
{
  uint32_t* r = start;
  uint32_t  n;

  for (n = 0; n < p; n++) 
  {
    // generate an entry for each neuron: n.
    r[8*n]   = 1;
    r[8*n+1] = (3584 << 16) |
               (delay << SYNAPSE_TYPE_INDEX_BITS) |
               (((n+1) == p)? 0: (n+1));

  }
  return (start);
}


// The following function can be used to initialize the master
// population. It is used as part of the unit testing harness.

void initialize_master_population (void)
{
  master_population[0] = 2;
  master_population[1] = 2;
  master_population[2] = (32 << 3) | 7;
    //HACK!!! DRL must change...
}

// The following function will generate a random synaptic row,
// and is intended for unit testing.

synaptic_row_t generate_random_synaptic_row (void)
{
  uint8_t   n = ((random() >> 20) & 0xFF); // gives value in range 0-255.
  synaptic_row_t r = (synaptic_row_t) malloc ((n+1)*sizeof(uint32_t));
  uint32_t  i;

  r[0] = (uint32_t)n;

  for (i = 1; i < n; i++) {
    r[i] = random();                          // random returns 0.. 2^31-1 ...
    r[i] = (((r[i] & 0x7FFF8000) << 1  ) |    // ... so shift weight up 1 bit
              (sparse_delay(r[i]) << SYNAPSE_TYPE_INDEX_BITS) |
                                              // ... mask out delay bits
              (((r[i] >> (SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_INDEX_BITS) & 3) == 0)
                      << SYNAPSE_INDEX_BITS) |// ... shifted into type position
              (r[i] & SYNAPSE_INDEX_MASK));   //  ... retain random index
  }

  return (r);
}

void print_currents (void)
{
  bool empty = true;
  current_t c;

  printf ("Currents\n");

  for (index_t i = 0; i < num_neurons; i ++)
  {
    empty = empty && (bitsk (get_exc_neuron_input(i) - get_inh_neuron_input(i)) == 0);
  }
  
  if (!empty) 
  {
    printf ("-------------------------------------\n");

    for (index_t i = 0; i < num_neurons; i ++) 
    {
      c = get_exc_neuron_input(i) - get_inh_neuron_input(i);
      if (bitsk (c) != 0)
      {
        printf ("%3u: %12.6k (= ", i, c);
        print_current_equation(i);
        printf(")\n");
      }
    }
    printf ("-------------------------------------\n");
  }
}

#else /*DEBUG*/
void print_ring_buffers      (void)                   { return; }
void print_master_population (void)                   { return; }
void print_row_size_table    (void)                   { return; }
void print_synaptic_rows     (uint32_t* rows)         { use(rows); return; }
void print_synaptic_row      (synaptic_row_t synaptic_row) { use(synaptic_row); return; }
void print_currents          (void)                   { return; }
#endif /*DEBUG*/
