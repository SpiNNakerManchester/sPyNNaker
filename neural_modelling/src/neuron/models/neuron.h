#ifndef _NEURON_
#define _NEURON_

// for required types & some macros
#include "maths-util.h"

// forward declaration of neuron type
typedef struct neuron_t* neuron_pointer_t;

// setup function which needs to be called in main program before any neuron
// code executes currently minimum 100, then in 100 steps...  if not called
// then defaults to 1ms timestep
void neuron_set_machine_timestep(uint16_t microsecs);

// primary function called in timer loop after synaptic updates
bool neuron_state_update(REAL exc_input, REAL inh_input,
        neuron_pointer_t neuron);

/*
 * NB in the following 2 functions and in neuron code in general; parameters,
 * lists, loops etc go from 1..n (not 0..n-1) i.e. just like IN REAL LIFE
 * (and MATLAB, Fortran, Mathematica, R).  This is in order to help scientists,
 * mathematicians, statisticans, economists and other non-IT people retain their
 * sanity, and me to avoid writing bugs
 */
// set the neuron state variable(s)
void neuron_set_state(uint8_t i, REAL stateVar[], neuron_pointer_t neuron);

// get the neuron state variable(s)
REAL neuron_get_state(uint8_t i, restrict neuron_pointer_t neuron);

// access number of state variables, number of parameters & size of the per
// neuron data structure
void neuron_get_info(uint8_t *num_state_vars, uint16_t *struct_size);

// printout of neuron definition and state variables
void neuron_print(restrict neuron_pointer_t neuron);

#endif // _NEURON_H_
