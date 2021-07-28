#ifndef _NEURON_MODEL_MY_IMPL_H_
#define _NEURON_MODEL_MY_IMPL_H_

#include <neuron/models/neuron_model.h>

typedef struct neuron_t {
    // TODO: Parameters - make sure these match with the Python code,
    // including the order of the variables when returned by
    // get_neural_parameters.

    // Variable-state parameters e.g. membrane voltage
    REAL V;
    // offset current [nA]
    REAL I_offset;
    // Put anything else you want to store per neuron
    REAL my_parameter;
} neuron_t;

typedef struct global_neuron_params_t {
    // TODO: Add any parameters that apply to the whole model here (i.e. not
    // just to a single neuron)

    // Note: often these are not user supplied, but computed parameters

    uint32_t machine_time_step;
} global_neuron_params_t;

#endif // _NEURON_MODEL_MY_IMPL_H_
