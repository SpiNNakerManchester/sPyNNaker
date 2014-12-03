/****h* spin-neuron/spin-neuron-impl.h
 *  NAME
 *    spin-neuron-impl.h
 *
 *  DESCRIPTION
 *    Internal header file for SpiNNaker Neuron Modelling
 *
 *  COPYRIGHT
 *    (c) 2013, Dave Lester, The University of Manchester
 *
 *  CREATION DATE
 *    21 July, 2013
 *
 *  HISTORY
 *
 *********/

/*
 * Data representation in sparse psp:
 * 
 * +----------+----------+----------+----------+
 * |       weight        |   delay x|   index  |
 * +----------+----------+----------+----------+
 *
 * Standard Default layout:
 *
 *   [31:16] weight is 16 bits,
 *   [12:9]  delay  is 4 bits,
 *   [8]     x      is an optional one bit indicating whether
 *                       we need seperate excitatory/inhibitory synapses. 
 *   [7:0]   index  is 8 bits of neuron index.
 *
 * We can manipulate the quantities in delay/x/index, provided the
 * total is less than or equal to 13 (for 32 bit buffers), or 14
 * (for 16 bit buffers).
 *
 */

#ifndef __SPIN_NEURON_IMPL_H__
#define __SPIN_NEURON_IMPL_H__

#include "spin1_api.h"
#include "spin-neuron-typedefs.h"
#include "../common/common-impl.h"

#include <stdbool.h>

// Neuron scaling data

extern uint32_t       h;

// Neuron modelling data
extern voltage_t  v_membrane       [MAX_NEURON_SIZE];
extern voltage_t  v_reset          [MAX_NEURON_SIZE];
extern voltage_t  v_threshold      [MAX_NEURON_SIZE];
extern voltage_t  v_rest           [MAX_NEURON_SIZE];
extern decay_t    p22              [MAX_NEURON_SIZE];
extern decay_t    p21              [MAX_NEURON_SIZE];
extern uint8_t    refractory_clock [MAX_NEURON_SIZE];

extern uint32_t   time;

extern uint32_t num_neurons;
extern uint32_t key; // upper part of spike packet identifier

// Propagator multiplications

static inline s1615 decay_s1615 (s1615 x, decay_t d)
{
  int64_t s = (int64_t)(bitsk(x));
  int64_t u = (int64_t)(bitsulr(d));

  return (kbits ((int_k_t)((s*u) >> 32)));
}

static inline u1616 decay_u1616 (u1616 x, decay_t d)
{
  uint64_t s = (uint64_t)(bitsuk(x));
  uint64_t u = (uint64_t)(bitsulr(d));

  return (ukbits ((uint_uk_t)((s*u) >> 32)));
}

static inline s015 decay_s015 (s015 x, decay_t d)
{
  int64_t s = (int64_t)(bitsk(x));
  int64_t u = (int64_t)(bitsulr(d));

  return (rbits ((int_r_t)((s*u) >> 32)));
}

static inline u016 decay_u016 (u016 x, decay_t d)
{
  uint64_t s = (uint64_t)(bitsuk(x));
  uint64_t u = (uint64_t)(bitsulr(d));

  return (urbits ((uint_ur_t)((s*u) >> 32)));
}

// Get index into current buffer of current input for specified neuron on specified synapse type
static inline index_t input_current_offset(index_t neuron_id, index_t synapse_type)
{
  return ((synapse_type << SYNAPSE_INDEX_BITS) | neuron_id);
}

// The following permits us to do a type-generic macro for decay manipulation
#define decay(x,d)						      \
  ({								      \
    __typeof__ (x) tmp = (x);					      \
    if      (__builtin_types_compatible_p (__typeof__(x), s1615))     \
      tmp = decay_s1615 (x,d);					      \
    else if (__builtin_types_compatible_p (__typeof__(x), u1616))     \
      tmp = decay_u1616 (x,d);					      \
    else if (__builtin_types_compatible_p (__typeof__(x), s015))      \
      tmp = decay_s015 (x,d);					      \
    else if (__builtin_types_compatible_p (__typeof__(x), u016))      \
      tmp = decay_u016 (x,d);					      \
    else							      \
      abort (1);						      \
    tmp;							      \
})

// Function declarations in spin-neuron-configuration.c
bool system_load_dtcm ();

// Function declarations for synapses.c
void initialize_current_buffer      (void);
int configure_p11                   (uint32_t n, uint32_t* a, uint32_t flags);
void ring_buffer_transfer           (void);
int  synaptic_row                   (address_t*, size_t*, spike_t);
void process_synaptic_row           (synaptic_row_t row, bool write);
void reset_ring_buffer              (void);
bool row_size_table_filled          (uint32_t* address, uint32_t flags);
bool master_population_table_filled (uint32_t* address, uint32_t flags);
bool synaptic_data_filled           (uint32_t* address, uint32_t flags);
bool synaptic_current_data_filled   (uint32_t* address, uint32_t flags);
void print_weight                   (index_t synapse_type, weight_t w);
void print_current_buffer           (void);
void print_currents                 (void);

// Function declarations for spin1-api-harness.c
void set_up_and_request_synaptic_dma_write();

// **TODO** This Spin1 API-specific stuff doesn't really belong here
void initialise_dma_buffers();
void timer_callback (uint unused0, uint unused1);
void dma_callback(uint unused, uint tag);
void incoming_spike_callback (uint key, uint payload);
void feed_dma_pipeline (uint unused0, uint unused1);

// Function declarations for neuron.c
void  neuron                (index_t n);
bool  neural_data_filled    (uint32_t* address, uint32_t flags);
void  print_neuron          (index_t n);
void  print_neurons         (void);

// Functions declared within a learning rule
void initialise_plasticity_buffers();
bool plasticity_region_filled (uint32_t *address, uint32_t flags);
void process_plastic_synapses (address_t plastic, address_t fixed, ring_entry_t *ring_buffer);
void print_plastic_synapses(address_t plastic, address_t fixed);
void plasticity_process_post_synaptic_event(uint32_t neuron_index);
accum plasticity_get_intrinsic_bias(uint32_t j);

// Function declarations for test.c
void      print_synaptic_row (uint32_t* synaptic_row);
uint32_t* generate_random_synaptic_row (void);
uint32_t* generate_synfire_chain(uint32_t* start, uint32_t delay, uint32_t p);
void      print_ring_buffers           (void);
void print_router_table      (uint n, uint32_t* key, uint32_t* mask, uint32_t* route);
void echo_router_table       (void);
void configure_router_table (uint32_t n, uint32_t* key, uint32_t* mask, uint32_t* route);
void print_router_bit (uint32_t m, uint32_t k);
void print_dma_buffers (void);
void initialize_master_population(void);
void print_master_population(void);
void print_sdram (uint32_t start, uint32_t items);
void print_row_size_table (void);
void print_synaptic_rows (uint32_t* rows);

#endif /* __SPIN_NEURON_IMPL_H__ */
