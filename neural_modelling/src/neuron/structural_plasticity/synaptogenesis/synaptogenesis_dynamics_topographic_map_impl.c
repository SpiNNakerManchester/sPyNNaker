/*! \file
 *
 *  \brief This file contains the main functions for topographic map formation,
 *  i.e. probabilistic synaptogenesis.
 *
 */

#include "../synaptogenesis_dynamics.h"
#include "../../../common/maths-util.h"

#include <random.h>
#include <spin1_api.h>
#include <debug.h>


//---------------------------------------
// Structures and global data
//---------------------------------------
typedef struct {
    uint32_t no_vertices;
    uint32_t *key_atom_info;
} subpopulation_info_t;

typedef struct {
    uint16_t no_pre_pops, max_subpartitions;
    subpopulation_info_t * pop_info;
} pre_pop_info_table_t;

typedef struct {
    int32_t p_rew, s_max, app_no_atoms, machine_no_atoms, low_atom, high_atom;
    REAL sigma_form_forward, sigma_form_lateral, p_form_forward, p_form_lateral, p_elim_dep, p_elim_pot;
    mars_kiss64_seed_t seed;
    pre_pop_info_table_t pre_pop_info_table;
} rewiring_data_t;

rewiring_data_t rewiring_data;

//---------------------------------------
// Initialisation
//---------------------------------------

address_t synaptogenesis_dynamics_initialise(
    address_t afferent_populations){
    // Read in all of the parameters from SDRAM

    rewiring_data.p_rew = &afferent_populations[0];
    log_error("P_REW ->> %d", rewiring_data.p_rew);
    return afferent_populations;
}

// Might need to function for rewiring. One to be called by the timer to generate
// a fake spike and trigger a dma callback
// and one to be called by the dma callback and then call formation or elimination

void synaptogenesis_dynamics_rewire(){
    log_error("Error you piece of shit!");
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
    return rewiring_data.p_rew;
}