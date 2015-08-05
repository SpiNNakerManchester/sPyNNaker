#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include "../common/neuron-typedefs.h"

bool spike_processing_initialise(size_t row_max_n_bytes);

void spike_processing_finish_write(uint32_t process_id);

void spike_processing_print_buffer_overflows();

#endif // _SPIKE_PROCESSING_H_
