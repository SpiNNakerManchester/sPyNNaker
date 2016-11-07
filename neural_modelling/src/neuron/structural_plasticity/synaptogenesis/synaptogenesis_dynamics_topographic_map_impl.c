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
    log_info("Structurally plastic implementation.");
    // Read in all of the parameters from SDRAM
    int32_t *sp_word = (int32_t*) afferent_populations;
//    int32_t offset = 0;
//    rewiring_data.p_rew = (int32_t)&afferent_populations[offset];
//    offset += 4;
//    rewiring_data.s_max = (int32_t)&afferent_populations[offset];
    rewiring_data.p_rew = *sp_word++;
    rewiring_data.s_max = *sp_word++;
    rewiring_data.sigma_form_forward = *(REAL*)sp_word++;
    rewiring_data.sigma_form_lateral = *(REAL*)sp_word++;
    rewiring_data.p_form_forward = *(REAL*)sp_word++;
    rewiring_data.p_form_lateral = *(REAL*)sp_word++;
    rewiring_data.p_elim_dep = *(REAL*)sp_word++;
    rewiring_data.p_elim_pot = *(REAL*)sp_word++;

    log_error("P_REW ->> %d", rewiring_data.p_rew);
    log_error("S_MAX ->> %d", rewiring_data.s_max);
    log_error("sigma_form_forward ->> %k", rewiring_data.sigma_form_forward);
    log_error("sigma_form_lateral ->> %k", rewiring_data.sigma_form_lateral);
    log_error("p_form_forward ->> %k", rewiring_data.p_form_forward);
    log_error("p_form_lateral ->> %k", rewiring_data.p_form_lateral);
    log_error("p_elim_dep ->> %k", rewiring_data.p_elim_dep);
    log_error("p_elim_pot ->> %k", rewiring_data.p_elim_pot);
//    rt_error(RTE_SWERR);
    return afferent_populations;
}

// Might need to function for rewiring. One to be called by the timer to generate
// a fake spike and trigger a dma callback
// and one to be called by the dma callback and then call formation or elimination

void synaptogenesis_dynamics_rewire(){
//    log_error("Error you piece of shit!");
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