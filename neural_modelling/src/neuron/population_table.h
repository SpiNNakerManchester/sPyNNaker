#ifndef _POPULATION_TABLE_H_
#define _POPULATION_TABLE_H_

#include "../common/neuron-typedefs.h"

bool population_table_initialise(address_t table_address,
                                 address_t synapse_rows_address,
                                 uint32_t *row_max_n_words);

bool population_table_get_address(spike_t spike, address_t* row_address,
                                  size_t* n_bytes_to_transfer);

#endif // _POPULATION_TABLE_H_
