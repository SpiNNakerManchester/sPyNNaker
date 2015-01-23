#include "../common/neuron-typedefs.h"

void population_table_initialise(address_t address);

bool population_table_get_address(uint32_t spike, address_t row_address,
        size_t n_bytes_to_transfer);
