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
#include <stdfix-full-iso.h>


//---------------------------------------
// Structures and global data
//---------------------------------------
typedef struct {
    int32_t no_pre_vertices;
    int32_t *key_atom_info;
} subpopulation_info_t;

typedef struct {
    int32_t no_pre_pops;
    subpopulation_info_t * subpop_info;
} pre_pop_info_table_t;

typedef struct {
    int32_t p_rew, s_max, app_no_atoms, machine_no_atoms, low_atom, high_atom;
    REAL sigma_form_forward, sigma_form_lateral, p_form_forward, p_form_lateral, p_elim_dep, p_elim_pot;
    mars_kiss64_seed_t shared_seed, my_seed;
    pre_pop_info_table_t pre_pop_info_table;
} rewiring_data_t;

rewiring_data_t rewiring_data;

//---------------------------------------
// Initialisation
//---------------------------------------

address_t synaptogenesis_dynamics_initialise(
    address_t afferent_populations){
    log_info("SP implementation");
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

    rewiring_data.app_no_atoms = *sp_word++;
    rewiring_data.low_atom = *sp_word++;
    rewiring_data.high_atom = *sp_word++;
    rewiring_data.machine_no_atoms = *sp_word++;

    rewiring_data.shared_seed[0] = *sp_word++;
    rewiring_data.shared_seed[1] = *sp_word++;
    rewiring_data.shared_seed[2] = *sp_word++;
    rewiring_data.shared_seed[3] = *sp_word++;

    rewiring_data.pre_pop_info_table.no_pre_pops = *sp_word++;

    // Need to malloc space for subpop_info, i.e. an array containing information for each pre-synaptic
    // application vertex

    rewiring_data.pre_pop_info_table.subpop_info = (subpopulation_info_t*) sark_alloc(\
        rewiring_data.pre_pop_info_table.no_pre_pops, sizeof(subpopulation_info_t));

    int32_t index;
    for (index = 0; index < rewiring_data.pre_pop_info_table.no_pre_pops; index ++) {
        // Read the actual number of presynaptic subpopulations
        rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices = *sp_word++;
        rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info =  (int32_t*) sark_alloc(\
            2 * rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices, sizeof(int32_t));
        int32_t subpop_index;
        for (subpop_index = 0; subpop_index < 2 * rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices; subpop_index++) {
            // key
            rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info[subpop_index++] = *sp_word++;
            // n_atoms
            rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info[subpop_index] = *sp_word++;
        }
    }

    // Setting up RNG
    validate_mars_kiss64_seed(rewiring_data.shared_seed);
    return (address_t)sp_word;
}

// Might need to function for rewiring. One to be called by the timer to generate
// a fake spike and trigger a dma callback
// and one to be called by the dma callback and then call formation or elimination

void synaptogenesis_dynamics_rewire(){
    // Randomly choose a postsynaptic (application neuron)
    int32_t id;
    id = lrbits(mars_kiss64_seed(rewiring_data.shared_seed)) * rewiring_data.app_no_atoms;
    // Check if neuron is in the current machine vertex
    if (id < rewiring_data.low_atom || id > rewiring_data.high_atom) {
        return;
    }
    // If it is, select a presynaptic population
    // I SHOULDN'T USE THE SAME SEED AS THE OTHER POPULATIONS HERE AS IT WILL MESS UP
    // RN GENERATION ON DIFFERENT CORES
    uint32_t pre_app_pop = ulrbits(mars_kiss64_seed(rewiring_data.my_seed)) * rewiring_data.pre_pop_info_table.no_pre_pops;
    // TODO Select presynaptic subpopulation
    // TODO Select a presynaptic neuron id
    // TODO Trigger DMA_read of the row corresponding to that synaptic row
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