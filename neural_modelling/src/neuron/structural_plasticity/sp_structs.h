#ifndef _SP_STRUCTS_H_
#define _SP_STRUCTS_H_

#include <neuron/synapse_row.h>

typedef struct {
    weight_t weight;
    uint32_t delay;
    uint32_t offset;
} structural_plasticity_data_t;

#endif // _SP_STRUCTS_H_
