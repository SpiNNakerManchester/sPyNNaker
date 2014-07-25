#ifndef DUAL_EXCITATORY_EXPONENTIAL_H
#define DUAL_EXCITATORY_EXPONENTIAL_H

#include "../../neuron/spin-neuron-impl.h"

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 3

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
	decay_t neuron_synapse_decay;
	decay_t neuron_synapse_init;
} synapse_param_t;

//---------------------------------------
// Externals
//---------------------------------------
extern current_t *current;
extern synapse_param_t *neuron_synapse_params[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------
static inline index_t ex1_offset (index_t n) { return input_current_offset(n, 0); }
static inline index_t ex2_offset (index_t n) { return input_current_offset(n, 1); }
static inline index_t in_offset (index_t n) { return input_current_offset(n, 2); }

static inline decay_t ex1_decay(index_t n)
{
  return (neuron_synapse_params[0][n].neuron_synapse_decay);
}
static inline decay_t ex2_decay(index_t n)
{
  return (neuron_synapse_params[1][n].neuron_synapse_decay);
}
static inline decay_t in_decay(index_t n)
{
  return (neuron_synapse_params[2][n].neuron_synapse_decay);
}

// Exponential shaping
//
// This is used to give a simple exponential decay to synapses.
//
// If we have combined excitatory/inhibitory synapses it will be
// because both excitatory and inhibitory synaptic time-constants
// (and thus propogators) are identical.

static inline void shape_current(index_t n)
{
  current[ex1_offset(n)] = decay_s1615(current[ex1_offset(n)], ex1_decay(n));
  current[ex2_offset(n)] = decay_s1615(current[ex2_offset(n)], ex2_decay(n));
  current[in_offset(n)] = decay_s1615(current[in_offset(n)], in_decay(n));
}

static inline current_t get_exc_neuron_input(index_t n)
{ 
  return (current[ex1_offset(n)] + current[ex2_offset(n)]); 
}

static inline current_t get_inh_neuron_input (index_t n)
{
  return current[in_offset(n)];
}

static inline void add_neuron_input(index_t neuron_id, index_t synapse_type,
		current_t input)
{
  current[input_current_offset(neuron_id, synapse_type)] += decay_s1615(input,
      1 - neuron_synapse_params[synapse_type][neuron_id].neuron_synapse_init);
}

#ifdef DEBUG
static inline const char *get_synapse_type_char(index_t s)
{
  if(s == 0)
  {
    return "X";
  }
  else if(s == 1)
  {
    return "X2";
  }
  else
  {
    return "I";
  }
}

static inline void print_current_equation(index_t n)
{
  printf("%12.6k + %12.6k - %12.6k",
    current[ex1_offset(n)], current[ex2_offset(n)], current[in_offset(n)]
  );
}
#endif  // DEBUG

#endif  // DUAL_EXCITATORY_EXPONENTIAL_H
