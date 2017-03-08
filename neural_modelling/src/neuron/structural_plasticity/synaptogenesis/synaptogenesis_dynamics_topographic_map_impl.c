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

#include "../../synapse_row.h"

#include "../../synapses.h"
#include "../../plasticity/synapse_dynamics.h"

#include "../../../common/neuron-typedefs.h"
#include "../../../common/sp_structs.h"





//---------------------------------------
// Structures and global data
//---------------------------------------
// DMA tags
#define DMA_TAG_READ_SYNAPTIC_ROW 0
#define DMA_TAG_WRITE_PLASTIC_REGION 1
#define DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING 2


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

typedef struct {

    // Address in SDRAM to write back plastic region to
    address_t sdram_writeback_address;

    // Key of originating spike
    // (used to allow row data to be re-used for multiple spikes)
    spike_t originating_spike;

    uint32_t n_bytes_transferred;

    // Row data
    uint32_t *row;

} dma_buffer_t;

dma_buffer_t rewiring_dma_buffer;

typedef struct {
    address_t sdram_synaptic_row;
    int32_t pre_syn_id, post_syn_id;
    structural_plasticity_data_t sp_data;
} current_state_t;

current_state_t current_state;

//typedef struct {
//
//} synaptic_row_pointers_t;
//synaptic_row_pointers_t synaptic_row_pointers

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
    log_info("Synaptogenesis (Topographic map) init.");
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

    // Setting up DMA buffers
    rewiring_dma_buffer.row = (uint32_t*) spin1_malloc(
                rewiring_data.s_max * sizeof(uint32_t));
    if (rewiring_dma_buffer.row == NULL) {
        log_error("Could not initialise DMA buffers");
        rt_error(RTE_SWERR);
    }

    log_info("Synaptogenesis init complete.");
    return (address_t)sp_word;
}

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] None
//! \return None


void synaptogenesis_dynamics_rewire(){
    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id;
    post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) * rewiring_data.app_no_atoms;
    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom || post_id > rewiring_data.high_atom) {
        log_debug("Selected neuron is not my problem (%d)", post_id);
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
        log_error("Failed find synaptic row address@key %d", fake_spike);
    }
    // Saving current state
    current_state.sdram_synaptic_row = synaptic_row_address;
    current_state.pre_syn_id = choice;
    current_state.post_syn_id = post_id;

    log_debug("Reading %d bytes from %d -- saved @ %d", n_bytes, synaptic_row_address, rewiring_dma_buffer.row);

    uint dma_id;
    dma_id = spin1_dma_transfer(
        DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING, synaptic_row_address, rewiring_dma_buffer.row, DMA_READ,
        n_bytes);
    if(!dma_id){
        log_info("DMA Queue full. Synaptic rewiring request failed!");
    }
}

// Might need a function for rewiring. One to be called by the timer to generate
// a fake spike and trigger a dma callback
// and one to be called by the dma callback and then call formation or elimination
void synaptic_row_restructure(){
    /*
        I need to know the structure of the row, know where to look for the postsynaptic neuron id.
            -- I need to use synapse_row_fixed_region(row) to retrieve the fixed region within the row  ✓
            -- then, synapse_row_plastic_controls(fixed) to retrieve the "controls" ✓
            -- also, figure out what type of weight struct is being used, to reclaim the sizeof(weights) ✓
        Then
            if this neuron id exists
                remove it
                update count values (how many neurons etc)
                    // Within the fixed-region extracted using the above API, fixed[0]
                    // Contains the number of 32-bit fixed synaptic words, fixed[1]
                    // Contains the number of 16-bit plastic synapse control words
                remove weight
                shift data around so it is contiguous
            else
                add the id to the structure storing ids (presumably at the end of the structure)
                add its weight to the structure storing the weight
                update count values
                    // Within the fixed-region extracted using the above API, fixed[0]
                    // Contains the number of 32-bit fixed synaptic words, fixed[1]
                    // Contains the number of 16-bit plastic synapse control words

         There could be some timing related issues, i.e. I need to remove the trace information for the specific
         neuron I'm removing / add specific timing info for new neurons.

    */
    // If I am here, then the DMA read was successful. As such, the synaptic row is in rewiring_dma_buffer, while
    // the selected pre and postsynaptic ids are in current_state
    // typedef uint32_t size_t;
//    address_t fixed_region = synapse_row_fixed_region(rewiring_dma_buffer.row);
//    address_t plastic_region = synapse_row_plastic_region(rewiring_dma_buffer.row);
//    control_t* plastic_controls = synapse_row_plastic_controls(fixed_region);

//    #if STDP_ENABLED == 1
//    bool hit = find_plastic_neuron_with_id(current_state.post_syn_id, rewiring_dma_buffer.row, &(current_state.sp_data));
//    if (hit) {
//        log_info("HIT - %d", current_state.sp_data.offset);
//    }
//    else {
//        log_info("MISS - %d", current_state.sp_data.offset);
//    }
//    #else
//
//    #endif
    bool (*search_for_neuron)(uint32_t, address_t, structural_plasticity_data_t *);
    bool (*remove_neuron)(uint32_t, address_t);
    bool (*add_neuron)(uint32_t, address_t, uint32_t, uint32_t);

    #if STDP_ENABLED == 1
        search_for_neuron = &find_plastic_neuron_with_id;
        remove_neuron = &remove_plastic_neuron_at_offset;
        add_neuron = &add_plastic_neuron_with_id;
    #else
        search_for_neuron = &find_static_neuron_with_id;
        remove_neuron = &remove_static_neuron_at_offset;
        add_neuron = &add_static_neuron_with_id;
    #endif

    bool hit= search_for_neuron(current_state.post_syn_id, rewiring_dma_buffer.row, &(current_state.sp_data));
    if (hit) {
        if(remove_neuron(current_state.sp_data.offset, rewiring_dma_buffer.row)){
            // TODO - SAVE THE ROW BACK IN SDRAM
            ;
        }
        log_info("HIT - %d", current_state.sp_data.offset);
    }
    else {
        // TODO Don't forget about these hardcoded values, which might not be sensible
        if(add_neuron(current_state.sp_data.offset, rewiring_dma_buffer.row, 0, 1)){
            // TODO - SAVE THE ROW BACK IN SDRAM
            ;
        }
        log_info("MISS - %d", current_state.sp_data.offset);
    }

}

 /*
    TODO:
    Formation and elimination are structurally agnostic, i.e. they don't care how
    synaptic rows are organised in physical memory.

    As such, they need to call functions that have a knowledge of how the memory is
    physically organised to be able to modify Plastic-Plastic synaptic regions.
 */
bool synaptogenesis_dynamics_formation_rule(){
    return false;
}

bool synaptogenesis_dynamics_elimination_rule(uint32_t row_position, uint32_t weight){
    use(row_position);
    use(weight);
    return false;
}

int32_t get_p_rew() {
    return rewiring_data.p_rew;
}