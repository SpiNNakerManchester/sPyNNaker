

#ifndef _GENERIC_NEURON_
#define _GENERIC_NEURON_


// for required types & some macros
#include "maths-util.h"   


// forward declaration of neuron type
typedef struct neuron_t* neuron_pointer_t; 


// primary function called in timer loop after synaptic updates - assumes current input (in nA?)
bool neuron_state_update( REAL exc_input, REAL inh_input, neuron_pointer_t neuron );


// solver or closed-form solution has just set new state variable values, so check for discrete state changes
void neuron_discrete_changes( neuron_pointer_t neuron );


#ifdef USING_ODE_SOLVER
// required when using ODE solver
void neuron_ode( REAL t, REAL stateVar[], REAL dstateVar_dt[], neuron_pointer_t neuron );
#endif

/*
 * NB in the following 2 functions and in neuron code in general; parameters, lists, loops etc go from 1..n 
 * (not 0..n-1) i.e. just like IN REAL LIFE (and MATLAB, Fortran, Mathematica, R).  This is in order to help 
 * scientists, mathematicians, statisticans, economists and other non-IT people retain their sanity, and me
 * to avoid writing bugs
 * 
 */
// set the neuron state variable(s)
void	neuron_set_state( uint8_t i, REAL stateVar[], neuron_pointer_t neuron );


// get the neuron state variable(s)
REAL neuron_get_state( uint8_t i, restrict neuron_pointer_t neuron );


// access number of state variables, number of parameters & size of the per neuron data structure
void neuron_get_info( uint8_t *num_state_vars, uint16_t *struct_size );


// printout of neuron definition and state variables
void neuron_print( restrict neuron_pointer_t neuron );


// setup function which needs to be called in main program before any neuron code executes
// currently minimum 100, then in 100 steps...  if not called then defaults to 1ms timestep
void provide_machine_timestep( uint16_t microsecs );


#endif   // include guard
