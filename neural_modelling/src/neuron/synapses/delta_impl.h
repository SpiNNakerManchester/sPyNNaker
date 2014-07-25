#ifndef DELTA_H
#define DELTA_H

#include "../../neuron/spin-neuron-impl.h"

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 0
#define SYNAPSE_TYPE_COUNT 1

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
} synapse_param_t;

//---------------------------------------
// Externals
//---------------------------------------
extern current_t *current;
extern synapse_param_t *neuron_synapse_params[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------
static inline index_t ex_offset (index_t n) { return input_current_offset(n, 0); }

// Delta_shaping
//
// This is used to give a simple exponential decay to synapses.
//
// If we have combined excitatory/inhibitory synapses it will be
// because both excitatory and inhibitory synaptic time-constants
// (and thus propogators) are identical.

static inline void shape_current(index_t n)
{
  current[ex_offset(n)] = 0;
}

static inline current_t get_exc_neuron_input (index_t n)
{ 
  return (current[ex_offset(n)]); 
}

static inline current_t get_inh_neuron_input (index_t n)
{
  return 0;
}

static inline void add_neuron_input(index_t neuron_id, index_t synapse_type,
		current_t input)
{
  // TODO: Check that the weight doesn't need to be scaled over time
  current[input_current_offset(neuron_id, synapse_type)] += input;
}

#ifdef DEBUG
static inline const char *get_synapse_type_char(index_t s)
{
  return "D";
}

static inline void print_current_equation(index_t n)
{
  printf("%12.6k",
    current[ex_offset(n)]
  );
}
#endif  // DEBUG


#endif  // DELTA_H
