#ifndef _SYNAPTOGENESIS_DYNAMICS_H_
#define _SYNAPTOGENESIS_DYNAMICS_H_

address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address);

void synaptogenesis_dynamics_rewire();

bool synaptogenesis_dynamics_formation_rule();

bool synaptogenesis_dynamics_elimination_rule(uint32_t row_position, uint32_t weight);

void synaptic_row_restructure();

int32_t get_p_rew();

#endif // _SYNAPTOGENESIS_DYNAMICS_H_
