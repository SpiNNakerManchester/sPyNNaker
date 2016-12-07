#include "synaptogenesis_dynamics.h"
#include <debug.h>

address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address){
	use(sdram_sp_address);
	log_info("Non-structurally plastic implementation.");
    return sdram_sp_address;
}

void synaptogenesis_dynamics_rewire(){
    log_error("There should be no structurally plastic synapses!");
}

void synapse_check(){
    log_error("There should be no structurally plastic synapses!");
}

address_t synaptogenesis_dynamics_formation_rule(address_t synaptic_row_address){
    use(synaptic_row_address);
    return NULL;
}

address_t synaptogenesis_dynamics_elimination_rule(address_t synaptic_row_address){
    use(synaptic_row_address);
    return NULL;
}

int32_t get_p_rew() {
    return -1;
}