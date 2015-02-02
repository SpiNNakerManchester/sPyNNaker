#ifndef _NEURON_MODEL_H_
#define _NEURON_MODEL_H_

#include "../../common/neuron-typedefs.h"

// forward declaration of neuron type
typedef struct neuron_t* neuron_pointer_t;

// setup function which needs to be called in main program before any neuron
// code executes currently minimum 100, then in 100 steps...  if not called
// then defaults to 1ms timestep
void neuron_model_set_machine_timestep(timer_t microsecs);

// Function that converts an input into the real value to be used by the neuron;
// Allows e.g. scaling of the neuron inputs for better precision
static input_t neuron_model_convert_input(input_t input);

// primary function called in timer loop after synaptic updates
bool neuron_model_state_update(input_t exc_input, input_t inh_input,
                               input_t external_bias, neuron_pointer_t neuron);

// get the neuron membrane voltage
state_t neuron_model_get_membrane_voltage(restrict neuron_pointer_t neuron);

// printout of neuron definition and state variables
void neuron_model_print(restrict neuron_pointer_t neuron);

#endif // _NEURON_MODEL_H_
