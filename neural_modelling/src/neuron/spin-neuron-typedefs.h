#ifndef SPIN_NEURON_TYPEDEFS_H
#define SPIN_NEURON_TYPEDEFS_H

#include <stdint.h>

// forward declaration of neuron type
typedef struct neuron_t* neuron_pointer_t; 

// Optionally change the following definition of PLASTIC_TAG_BITS
// for fewer or more tag bits for synapses. The default is 8 bits.

/*#ifndef PLASTIC_TAG_BITS
#define PLASTIC_TAG_BITS 8
#endif	// PLASTIC_TAG_BITS*/

// Do not change the defined values from here on...

//#define PLASTIC_TAG_MASK ((1 << (PLASTIC_TAG_BITS)) - 1)

typedef uint16_t control_t;
//typedef uint32_t tag_t;

#endif  // SPIN_NEURON_TYPEDEFS_H