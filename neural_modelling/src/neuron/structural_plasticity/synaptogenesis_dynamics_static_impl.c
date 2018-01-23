#include "synaptogenesis_dynamics.h"
#include <debug.h>

static const char* sp_error_message = "Non-structurally plastic implementation.";

address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address) {
    use(sdram_sp_address);
    log_debug("%s", sp_error_message);
    return sdram_sp_address;
}

void synaptogenesis_dynamics_rewire(
	uint32_t time) {
    use(time);
    log_error("%s", sp_error_message);
}

void synaptic_row_restructure(void) {
    log_error("%s", sp_error_message);
}

bool synaptogenesis_dynamics_formation_rule(void) {
    return false;
}

bool synaptogenesis_dynamics_elimination_rule(void) {
    return false;
}

int32_t get_p_rew(void) {
    return -1;
}

bool is_fast(void) {
    return false;
}

void update_goal_posts(
	uint32_t time) {
    use(time);
}
