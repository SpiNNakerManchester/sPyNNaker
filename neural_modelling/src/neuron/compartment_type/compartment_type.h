#ifndef _COMPARTMENT_TYPE_H_
#define _COMPARTMENT_TYPE_H_

#include <common/neuron-typedefs.h>

// Generates the value to be used in the ring buffer
static inline REAL compute_input_rate(uint32_t rate);

// Convert input rate to input current
static inline REAL get_input_current(REAL input, REAL weight);

#endif //_COMPARTMENT_TYPE_H_