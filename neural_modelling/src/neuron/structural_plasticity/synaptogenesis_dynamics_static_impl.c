/*! \file
 *
 * SUMMARY
 *  \brief This file contains the static impl of synaptogenesis.
 *  No functionality is gained with this class
 *
 */
#include "synaptogenesis_dynamics.h"
#include <debug.h>

address_t synaptogenesis_dynamics_initialise(
    address_t sdram_sp_address){
    use(sdram_sp_address);
    return sdram_sp_address;
}

bool synaptogenesis_dynamics_rewire(uint32_t time,
        spike_t *spike, address_t *synaptic_row_address, uint32_t *n_bytes) {
    use(time);
    use(spike);
    use(synaptic_row_address);
    use(n_bytes);
    return false;
}

bool synaptogenesis_row_restructure(uint32_t time, address_t row) {
    use(time);
    use(row);
    return false;
}

bool synaptogenesis_dynamics_formation_rule(uint32_t time, address_t row) {
    use(time);
    use(row);
    return false;
}

bool synaptogenesis_dynamics_elimination_rule(uint32_t time, address_t row) {
    use(time);
    use(row);
    return false;
}

int32_t synaptogenesis_rewiring_period() {
    return -1;
}

bool synaptogenesis_is_fast() {
    return false;
}

void update_goal_posts(uint32_t time) {
    use(time);
}
