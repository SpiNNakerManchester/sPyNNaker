/*! \file
 *
 *  \brief This file contains the main functions for topographic map formation,
 *  i.e. probabilistic synaptogenesis.
 *
 */
#include "../synaptogenesis_dynamics.h"
//#include "../../../common/maths-util.h"
#include "../../population_table/population_table.h"

#include <random.h>
#include <spin1_api.h>
#include <debug.h>
#include <stdfix-full-iso.h>

//---------------------------------------
// Structures and global data
//---------------------------------------

typedef struct {
    int32_t no_pre_vertices, total_no_atoms;
    int32_t *key_atom_info;
} subpopulation_info_t;

typedef struct {
    int32_t no_pre_pops;
    subpopulation_info_t * subpop_info;
} pre_pop_info_table_t;

typedef struct {
    int32_t p_rew, s_max, app_no_atoms, machine_no_atoms, low_atom, high_atom;
    REAL sigma_form_forward, sigma_form_lateral, p_form_forward, p_form_lateral, p_elim_dep, p_elim_pot;
    mars_kiss64_seed_t shared_seed, local_seed;
    pre_pop_info_table_t pre_pop_info_table;
} rewiring_data_t;

rewiring_data_t rewiring_data;

//---------------------------------------
// Initialisation
//---------------------------------------
//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//! parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address Address of the start of the SDRAM region
//! which contains synaptic rewiring params.
//! \return address_t Address after the final word read from SDRAM.

address_t synaptogenesis_dynamics_initialise(
    address_t sdram_sp_address){
    log_info("Synaptogenesis (Topographic map) implementation.");
    // Read in all of the parameters from SDRAM
    int32_t *sp_word = (int32_t*) sdram_sp_address;
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
        rewiring_data.pre_pop_info_table.subpop_info[index].total_no_atoms = *sp_word++;
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

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] None
//! \return None


void synaptogenesis_dynamics_rewire(){
    // Randomly choose a postsynaptic (application neuron)
    int32_t post_id;
    post_id = lrbits(mars_kiss64_seed(rewiring_data.shared_seed)) * rewiring_data.app_no_atoms;
    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom || post_id > rewiring_data.high_atom) {
        return;
    }
    post_id -= rewiring_data.low_atom;
    // If it is, select a presynaptic population
    // I SHOULDN'T USE THE SAME SEED AS THE OTHER POPULATIONS HERE AS IT WILL MESS UP
    // RN GENERATION ON DIFFERENT CORES
    uint32_t pre_app_pop = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * rewiring_data.pre_pop_info_table.no_pre_pops;
    // Select presynaptic subpopulation
    int32_t choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].total_no_atoms;
    int32_t i;
    int32_t sum=0;
    for(i=0;i<rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].no_pre_vertices; i++) {
        sum += rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[2 *i + 1];
        if (sum >= choice){
            break;
          }
    }

    // Select a presynaptic neuron id
    choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *\
     rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[2 *i + 1];

    // population_table_get_first_address() returns the address (in SDRAM) of the selected synaptic row

    address_t synaptic_row_address;
    spike_t fake_spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[2 *i] | choice;
    size_t n_bytes;

    if(!population_table_get_first_address(fake_spike, &synaptic_row_address, &n_bytes)) {
        log_error("Failed to retrieve synaptic row address for key %d", fake_spike);
    }

    // TODO Trigger DMA_read of the row corresponding to that synaptic row

}

 /*
    TODO:
    Formation and elimination are structurally agnostic, i.e. they don't care how
    synaptic rows are organised in physical memory.

    As such, they need to call functions that have a knowledge of how the memory is
    physically organised to be able to modify Plastic-Plastic synaptic regions.
 */
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