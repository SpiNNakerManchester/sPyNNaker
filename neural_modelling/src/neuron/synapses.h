#include "../common/neuron-typedefs.h"

void synapses_initialise(address_t address, uint32_t n_neurons);

void synapses_do_timestep_update();

void synapses_process_synaptic_row(synaptic_row_t row, bool write);
