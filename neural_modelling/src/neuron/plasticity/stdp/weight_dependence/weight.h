#ifndef _WEIGHT_H_
#define _WEIGHT_H_

#include "../../../../common/neuron-typedefs.h"

address_t weight_initialise(address_t address,
                            uint32_t *ring_buffer_to_input_buffer_left_shifts);

static weight_state_t weight_get_initial(weight_t weight, index_t synapse_type);

static weight_t weight_get_final(weight_state_t new_state);

#endif // _WEIGHT_H_
