#ifndef _SYNAPTOGENESIS_DYNAMICS_H_
#define _SYNAPTOGENESIS_DYNAMICS_H_
#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address);
void synaptogenesis_dynamics_rewire();
address_t synaptogenesis_dynamics_formation_rule(address_t synaptic_row_address);
address_t synaptogenesis_dynamics_elimination_rule(address_t synaptic_row_address);

int32_t get_p_rew();

#endif // _SYNAPTOGENESIS_DYNAMICS_H_
