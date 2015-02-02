#ifndef _NEURON_H_
#define _NEURON_H_

#include "../common/neuron-typedefs.h"
#include "../common/recording.h"

bool neuron_initialise(address_t address, uint32_t recording_flags,
                       uint32_t *n_neurons_value);

void neuron_set_input_buffers(input_t *input_buffers_value);

void neuron_do_timestep_update(uint32_t time);

#endif // _NEURON_H_
