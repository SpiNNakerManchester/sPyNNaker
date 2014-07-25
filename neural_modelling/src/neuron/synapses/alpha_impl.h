#ifndef ALPHA_H
#define ALPHA_H

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 4

//---------------------------------------
// Externals
//---------------------------------------
extern current_t *current;
extern synapse_param_t *neuron_synapse_params[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------
static inline index_t ex1_offset (index_t n) { return input_current_offset(n, 0); }
static inline index_t in1_offset (index_t n) { return input_current_offset(n, 1); }
static inline index_t ex2_offset (index_t n) { return input_current_offset(n, 2); }
static inline index_t in2_offset (index_t n) { return input_current_offset(n, 3); }

static inline decay_t ex1_decay(index_t n) { return (neuron_synapse_params[0][n]); }
static inline decay_t in1_decay(index_t n) { return (neuron_synapse_params[1][n]); }
// **FIXME**
static inline decay_t ex2_decay(index_t n) { return (neuron_synapse_params[0][n]); }
static inline decay_t in2_decay(index_t n) { return (neuron_synapse_params[1][n]); }

// shape alpha:
//
// Default values (iaf_psc_alpha.cpp/iaf_cond_exp.c)
//
// tau_x = 2.0ms  0.2ms
// tau_i = 2.0ms  2.0ms
//
// h /* current time step size in ms */
//
// p11x = p22x = exp (-h/tau_x)
// p11i = p22i = exp (-h/tau_i)
//
// p21x = h * p11x
// p21i = h * p11i
//
// y2x  = p21x * y1x + p22x * y2x;
// y1x *= p11x
//
// y2i  = p21i * y1i + p22i * y2i;
// y1i *= p11i
//
// then add in current ring_buffer inputs..
//
// y1x += /* scale* ? */ ring [n, x]
// y1i +=/* scale* ? */  ring [n, i]
// with scale 1/tau_x or tau_i as approrpiate?

static inline void shape_current(index_t n)
{
   if (SYNAPSE_ALPHA_BIT == 1) {// alpha synapses
    current[ex2_offset (n)] =  // y2x  = p21x * y1x + p22x * y2x;  
    // new ex current 2 = 
      decay_s1615 (current [ex1_offset (n)], p21_ex (n)) +
      decay_s1615 (current [ex2_offset (n)], p22_ex (n));

    current[in2_offset (n)] =  // y2i  = p21i * y1i + p22i * y2i
      decay_s1615 (current [in1_offset (n)], p21_in (n)) +
      decay_s1615 (current [in2_offset (n)], p22_in (n));
  }

  current [ex1_offset (n)]
    = decay_s1615 (current [ex1_offset (n)], p11_ex (n));

  if (SYNAPSE_TYPE_BITS == 1) // seperate inhibitory/excitatory currents
    current [in1_offset (n)]
      = decay_s1615 (current [in1_offset (n)], p11_in (n));
}

static inline current_t get_exc_neuron_input (index_t n)
{ 
  return (current[ex_offset(n)]); 
}

current_t get_inh_neuron_input (index_t n)
{
  return (current [in_offset (n)]);
}

static inline void add_neuron_input(index_t neuron_id, index_t synapse_type,
		current_t input)
{
  // TODO: Scale the input accordingly, to make sure that the weight is not
  // added too much!
  current[input_current_offset(neuron_id, synapse_type)] += input;
}
#endif  // ALPHA_H
