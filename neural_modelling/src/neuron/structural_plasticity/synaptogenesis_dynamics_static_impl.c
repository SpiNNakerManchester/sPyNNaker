#include "synaptogenesis_dynamics.h"
#include <debug.h>

static const char* sp_error_message = "Non-structurally plastic implementation.";

address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address){
	use(sdram_sp_address);
	log_info("%s", sp_error_message);
    return sdram_sp_address;
}

void synaptogenesis_dynamics_rewire(){
    log_error("%s", sp_error_message);
}

void synaptic_row_restructure(){
    log_error("%s", sp_error_message);
}

bool synaptogenesis_dynamics_formation_rule(){
    return false;
}

bool synaptogenesis_dynamics_elimination_rule(){
    return false;
}

int32_t get_p_rew() {
    return -1;
}