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
#include "../../../common/maths-util.h"
#include "../../../common/sp_structs.h"
#include "simulation.h"



//---------------------------------------
// External functions
//---------------------------------------
bool (*search_for_neuron)(uint32_t, address_t, structural_plasticity_data_t *);
bool (*remove_neuron)(uint32_t, address_t);
bool (*add_neuron)(uint32_t, address_t, uint32_t, uint32_t);
int (*number_of_connections_in_row)(address_t);


//---------------------------------------
// Structures and global data
//---------------------------------------
// DMA tags
//#define DMA_TAG_READ_SYNAPTIC_ROW 0
//#define DMA_TAG_WRITE_PLASTIC_REGION 1
#define DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING 5
#define DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING 7
#define KEY_INFO_CONSTANTS 3

#define MAX_SHORT 65535


typedef struct {
    int16_t no_pre_vertices, sp_control;
    int32_t total_no_atoms;
    int32_t *key_atom_info;
} subpopulation_info_t;

typedef struct {
    uint32_t no_pre_pops;
    subpopulation_info_t * subpop_info;
} pre_pop_info_table_t;

typedef struct {
    uint32_t p_rew, weight, delay, s_max, app_no_atoms, machine_no_atoms, low_atom, high_atom,\
        size_ff_prob, size_lat_prob, grid_x, grid_y, p_elim_dep, p_elim_pot;
    mars_kiss64_seed_t shared_seed, local_seed;
    pre_pop_info_table_t pre_pop_info_table;
    uint16_t *ff_probabilities, *lat_probabilities;
    uint32_t *synaptic_capacity;
} rewiring_data_t;

rewiring_data_t rewiring_data;

typedef struct {

    // Address in SDRAM to write back plastic region to
    address_t sdram_writeback_address;

    // Key of originating spike
    // (used to allow row data to be re-used for multiple spikes)
    spike_t originating_spike;

    size_t n_bytes_transferred;

    // Row data
    uint32_t *row;

    // DMA Tag
    uint dma_id;

} dma_buffer_t;

dma_buffer_t rewiring_dma_buffer;

typedef struct {
    address_t sdram_synaptic_row;
    uint32_t pre_syn_id, post_syn_id, distance;
    structural_plasticity_data_t sp_data;
    uint32_t current_time;
    int16_t current_controls;
    uint32_t global_pre_syn_id, global_post_syn_id;
} current_state_t;

current_state_t current_state;


static int my_abs(int a){
    return a < 0 ? -a : a;
}

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
    /*ad*/log_debug("SR init.");
    log_debug("Registering DMA callback");
    simulation_dma_transfer_done_callback_on(DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING, synaptic_row_restructure);
    log_debug("Callback registered");
    // Read in all of the parameters from SDRAM
    int32_t *sp_word = (int32_t*) sdram_sp_address;
    rewiring_data.p_rew = *sp_word++;
    rewiring_data.weight = *sp_word++;
    rewiring_data.delay = *sp_word++;
    rewiring_data.s_max = *sp_word++;

    rewiring_data.app_no_atoms = *sp_word++;
    rewiring_data.low_atom = *sp_word++;
    rewiring_data.high_atom = *sp_word++;
    rewiring_data.machine_no_atoms = *sp_word++;

    rewiring_data.grid_x = *sp_word++;
    rewiring_data.grid_y = *sp_word++;

    rewiring_data.p_elim_dep = *sp_word++;
    rewiring_data.p_elim_pot = *sp_word++;

    rewiring_data.shared_seed[0] = *sp_word++;
    rewiring_data.shared_seed[1] = *sp_word++;
    rewiring_data.shared_seed[2] = *sp_word++;
    rewiring_data.shared_seed[3] = *sp_word++;

    log_debug("p_rew %d weight %d delay %d s_max %d app_no_atoms %d lo %d hi %d machine_no_atoms %d x %d y %d p_elim_dep %d p_elim_pot %d",
        rewiring_data.p_rew,rewiring_data.weight, rewiring_data.delay, rewiring_data.s_max,
        rewiring_data.app_no_atoms, rewiring_data.low_atom, rewiring_data.high_atom, rewiring_data.machine_no_atoms,
        rewiring_data.grid_x, rewiring_data.grid_y,
        rewiring_data.p_elim_dep, rewiring_data.p_elim_pot
        );

    rewiring_data.pre_pop_info_table.no_pre_pops = *sp_word++;

    // Need to malloc space for subpop_info, i.e. an array containing information for each pre-synaptic
    // application vertex
    if (rewiring_data.pre_pop_info_table.no_pre_pops==0)
        return NULL;

    rewiring_data.pre_pop_info_table.subpop_info = (subpopulation_info_t*) sark_alloc(\
        rewiring_data.pre_pop_info_table.no_pre_pops, sizeof(subpopulation_info_t));

    uint32_t index;
    uint16_t *half_word;
    for (index = 0; index < rewiring_data.pre_pop_info_table.no_pre_pops; index ++) {
        // Read the actual number of presynaptic subpopulations
        half_word = (uint16_t*)sp_word;
        rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices = *half_word++;
        rewiring_data.pre_pop_info_table.subpop_info[index].sp_control = *half_word++;
        sp_word = (int32_t*) half_word;
        rewiring_data.pre_pop_info_table.subpop_info[index].total_no_atoms = *sp_word++;
        rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info =  (int32_t*) sark_alloc(\
            KEY_INFO_CONSTANTS * rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices, sizeof(int32_t));
        int32_t subpop_index;
        for (subpop_index = 0; subpop_index < KEY_INFO_CONSTANTS * rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices; subpop_index++) {
            // key
            rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info[subpop_index++] = *sp_word++;
            // n_atoms
            rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info[subpop_index++] = *sp_word++;
            // lo_atom
            rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info[subpop_index] = *sp_word++;
        }
    }

    // Read the probability vs distance tables into DTCM
    rewiring_data.size_ff_prob = *sp_word++;
    rewiring_data.ff_probabilities = (uint16_t*) sark_alloc(\
        rewiring_data.size_ff_prob, sizeof(uint16_t));
    log_debug("size ff lut %d", rewiring_data.size_ff_prob);
    half_word = (uint16_t*)sp_word;
    for (index = 0; index < rewiring_data.size_ff_prob; index++) {
        rewiring_data.ff_probabilities[index] = *half_word++;
        log_debug("ff_probabilities %d for index %d", rewiring_data.ff_probabilities[index], index);
    }

    sp_word = (int32_t*) half_word;
    rewiring_data.size_lat_prob = *sp_word++;

    log_debug("size lat lut %d", rewiring_data.size_lat_prob);
    rewiring_data.lat_probabilities = (uint16_t*) sark_alloc(\
        rewiring_data.size_lat_prob, sizeof(uint16_t));


    half_word = (uint16_t*)sp_word;
    for (index = 0; index < rewiring_data.size_lat_prob; index++) {
        rewiring_data.lat_probabilities[index] = *half_word++;
        log_debug("lat_probabilities %d for index %d",
            rewiring_data.lat_probabilities[index], index);
    }

    assert(((int)half_word)%4==4);

    sp_word = (int32_t*) half_word;

    // Read the synaptic capacity table
    rewiring_data.synaptic_capacity = (uint32_t*) sark_alloc(\
        rewiring_data.machine_no_atoms, sizeof(uint32_t));
    for (index = 0; index < rewiring_data.machine_no_atoms; index++) {
        rewiring_data.synaptic_capacity[index] = *sp_word++;
        log_debug("syn capacity %d for index %d", rewiring_data.synaptic_capacity[index], index);
    }


    // Setting up RNG
    validate_mars_kiss64_seed(rewiring_data.shared_seed);

    // Setting up DMA buffers
    rewiring_dma_buffer.row = (uint32_t*) sark_alloc(
                10 * rewiring_data.s_max, sizeof(uint32_t));
    if (rewiring_dma_buffer.row == NULL) {
        log_error("Fail init DMA buffers");
        rt_error(RTE_SWERR);
    }

    #if STDP_ENABLED == 1
        search_for_neuron = &find_plastic_neuron_with_id;
        remove_neuron = &remove_plastic_neuron_at_offset;
        add_neuron = &add_plastic_neuron_with_id;
        number_of_connections_in_row = &synapse_row_num_plastic_controls;
    #else
        search_for_neuron = &find_static_neuron_with_id;
        remove_neuron = &remove_static_neuron_at_offset;
        add_neuron = &add_static_neuron_with_id;
        number_of_connections_in_row = &synapse_row_num_fixed_synapses;
    #endif

    log_debug("rewiring_data.s_max %d", rewiring_data.s_max);
    /*ad*/log_debug("SR init complete.");
    return (address_t)sp_word;
}

//int dma_operation(int tag) {
//
//}

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] None
//! \return None
void synaptogenesis_dynamics_rewire(uint32_t time){
    current_state.current_time = time;
    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id;
    post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) * rewiring_data.app_no_atoms;
    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom || post_id > rewiring_data.high_atom) {
        log_debug("\t| NOTME %d @ %d", post_id, time);
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
        sum += rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[KEY_INFO_CONSTANTS * i + 1];
        if (sum >= choice){
            break;
          }
    }
    uint pre_sub_pop = i;
    // Select a presynaptic neuron id
    choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *\
        rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[KEY_INFO_CONSTANTS * pre_sub_pop + 1];
    // Log all random stuff
    /*ad*/log_debug("post_id %d pre_app_pop %d presynaptic subpopulation %d presynaptic neuron id %d", post_id, pre_app_pop, pre_sub_pop, choice);
    // population_table_get_first_address() returns the address (in SDRAM) of the selected synaptic row

    address_t synaptic_row_address;
    spike_t fake_spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[KEY_INFO_CONSTANTS * pre_sub_pop] | choice;
    size_t n_bytes;

    if(!population_table_get_first_address(fake_spike, &synaptic_row_address, &n_bytes)) {
//        log_error("FAIL@key %d", fake_spike);
        rt_error(RTE_SWERR);
    }
    // Saving current state
    current_state.sdram_synaptic_row = synaptic_row_address;
    current_state.pre_syn_id = choice;
    current_state.post_syn_id = post_id;
    current_state.current_controls = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].sp_control;

    log_debug("Reading %d bytes from %d saved %d", n_bytes, synaptic_row_address, rewiring_dma_buffer.row);


    // Compute the distance at this point to optimize CPU usage.
    // i.e. make use of it while servicing a DMA

    // To do this I need to take the DIV and MOD of the postsyn neuron id, of the presyn neuron id
    // Compute the distance of these 2 measures (start with Manhattan distance)
    int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;
    // TODO |Pre computation requires querying the table with global information
    // TODO | or see https://trello.com/c/fTM1BRh2/156-distance-based-rewiring-rules for alternative
    pre_global_id = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].key_atom_info[KEY_INFO_CONSTANTS * pre_sub_pop + 2] + current_state.pre_syn_id;
    post_global_id = current_state.post_syn_id + rewiring_data.low_atom;


    pre_x = pre_global_id / rewiring_data.grid_x;
    pre_y = pre_global_id % rewiring_data.grid_y;

    post_x = post_global_id / rewiring_data.grid_x;
    post_y = post_global_id % rewiring_data.grid_y;

    // With periodic boundary conditions
    uint delta_x, delta_y;
    delta_x = my_abs(pre_x - post_x);
    delta_y = my_abs(pre_y - post_y);

    if( delta_x > rewiring_data.grid_x>>1 )
        delta_x -= rewiring_data.grid_x;

    if( delta_y > rewiring_data.grid_y>>1 )
        delta_y -= rewiring_data.grid_y;

//    current_state.distance = my_abs(delta_x + delta_y);
    current_state.distance = delta_x * delta_x + delta_y * delta_y;
    current_state.global_pre_syn_id = pre_global_id;
    current_state.global_post_syn_id = post_global_id;

    /*ad*/log_debug("g_pre_id %d g_post_id %d g_distance_sq %d %d",
        pre_global_id, post_global_id, current_state.distance,
        current_state.current_controls
        );
    log_debug("pre_x %d pre_y %d", pre_x, pre_y);
    log_debug("post_x %d post_y %d", post_x, post_y);

    spin1_dma_transfer(
    DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING, synaptic_row_address, rewiring_dma_buffer.row, DMA_READ,
    n_bytes);
    rewiring_dma_buffer.n_bytes_transferred = n_bytes;
    rewiring_dma_buffer.sdram_writeback_address = synaptic_row_address;

}



// Might need a function for rewiring. One to be called by the timer to generate
// a fake spike and trigger a dma callback
// and one to be called by the dma callback and then call formation or elimination
void synaptic_row_restructure(uint dma_id, uint dma_tag){
    // If I am here, then the DMA read was successful. As such, the synaptic row is in rewiring_dma_buffer, while
    // the selected pre and postsynaptic ids are in current_state

    // Check that I'm actually servicing the correct row by checking
    // the current dma id with the one I received when I made the dma request
//    if (dma_id != rewiring_dma_buffer.dma_id)
//        log_error("Servicing invalid synaptic row!");
    use(dma_id);
    use(dma_tag);
    uint number_of_connections = number_of_connections_in_row(synapse_row_fixed_region(rewiring_dma_buffer.row));

    log_debug("no connections %d, synaptic_capacity of %d is %d",
    number_of_connections, current_state.post_syn_id,
    rewiring_data.synaptic_capacity[current_state.post_syn_id]
    );

    log_debug("rew current_weight %d", current_state.sp_data.weight);
    log_debug("sanity check delay %d", current_state.sp_data.delay);

    /*ad*/log_debug("sr_attempt %d %d", current_state.current_time, current_state.current_controls);

    // Is the row zero in length?
    bool zero_elements = number_of_connections == 0;
    // Does the neuron exist in the row?
    bool search_hit = search_for_neuron(current_state.post_syn_id, rewiring_dma_buffer.row, &(current_state.sp_data));

    // TODO Change this so that there's a decision between between creation and deletion
    // TODO based on the current number of existing vs open potential synaptic locations

    if (!zero_elements && search_hit) {

        synaptogenesis_dynamics_elimination_rule();
        // TODO check status of operation and save provenance (statistics)
    }
    else if(!search_hit && // TODO Check if there's space in the row
            rewiring_data.synaptic_capacity[current_state.post_syn_id] < rewiring_data.s_max &&
            number_of_connections < rewiring_data.s_max){
        log_debug("Synaptic capacity BEFORE %d", rewiring_data.synaptic_capacity[current_state.post_syn_id]);

        synaptogenesis_dynamics_formation_rule();
        log_debug("Synaptic capacity AFTER %d", rewiring_data.synaptic_capacity[current_state.post_syn_id]);

        // TODO check status of operation and save provenance (statistics)
    }
//    else {
//        log_debug("\t| NO REW");
//    }

}

 /*
    Formation and elimination are structurally agnostic, i.e. they don't care how
    synaptic rows are organised in physical memory.

    As such, they need to call functions that have a knowledge of how the memory is
    physically organised to be able to modify Plastic-Plastic synaptic regions.
 */
bool synaptogenesis_dynamics_elimination_rule(){
    // Is synaptic weight <.5 g_max?
    uint r = mars_kiss64_seed(rewiring_data.local_seed);
    /*ad*/log_debug("elim_prob r %u ctrl %d", r, current_state.current_controls);
    if( current_state.sp_data.weight < rewiring_data.weight >> 1 && r >= rewiring_data.p_elim_dep ){
        /*ad*/log_debug("\t| FAIL DEP %d", current_state.current_time);
        return false;
    }
    // otherwise use probability 2
    else if ( r >= rewiring_data.p_elim_pot ){
        /*ad*/log_debug("\t| FAIL POT %d", current_state.current_time);
        return false;
    }

    if(remove_neuron(current_state.sp_data.offset, rewiring_dma_buffer.row)){
        /*ad*/log_debug("\t| RM pre %d post %d # controls %d ctrl %d @ %d",
            current_state.global_pre_syn_id,
            current_state.global_post_syn_id,
            number_of_connections_in_row(synapse_row_fixed_region(rewiring_dma_buffer.row)),
            current_state.current_controls,
            current_state.current_time);
        rewiring_data.synaptic_capacity[current_state.post_syn_id]--;
        spin1_dma_transfer(
            DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING,
            rewiring_dma_buffer.sdram_writeback_address,
            rewiring_dma_buffer.row, DMA_WRITE,
            rewiring_dma_buffer.n_bytes_transferred);
        return true;
    }
    return false;
}

bool synaptogenesis_dynamics_formation_rule(){
    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;

    if( (current_state.current_controls == 0 && current_state.distance >= rewiring_data.size_ff_prob)
        || (current_state.current_controls == 1 && current_state.distance >= rewiring_data.size_lat_prob)){
        /*ad*/log_debug("\t| OOB %d %d %d",
            current_state.distance,
            current_state.current_time,
            current_state.current_controls);
        return false;
    }
    if( current_state.current_controls == 0 )
        probability = rewiring_data.ff_probabilities[current_state.distance];
    else
        probability = rewiring_data.lat_probabilities[current_state.distance];
    uint16_t r = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * MAX_SHORT;
//    uint16_t r = mars_kiss64_seed(rewiring_data.local_seed) & 0xFFFF;
    /*ad*/log_debug("form_prob %u vs r %u ctrl %d", probability, r, current_state.current_controls);
    if (r >= probability){
        /*ad*/log_debug("\t| NO FORM %d", current_state.current_time);
        return false;
    }

    if(add_neuron(current_state.post_syn_id, rewiring_dma_buffer.row,
            rewiring_data.weight, rewiring_data.delay)){
        /*ad*/log_debug("\t| FORM pre %d post %d # controls %d distance %d ctrl %d @ %d",
            current_state.global_pre_syn_id,
            current_state.global_post_syn_id,
            number_of_connections_in_row(synapse_row_fixed_region(rewiring_dma_buffer.row)),
            current_state.distance,
            current_state.current_controls,
            current_state.current_time);
        rewiring_data.synaptic_capacity[current_state.post_syn_id]++;
        spin1_dma_transfer(
            DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING,
            rewiring_dma_buffer.sdram_writeback_address,
            rewiring_dma_buffer.row, DMA_WRITE,
            rewiring_dma_buffer.n_bytes_transferred);
        return true;
    }
    return false;
}


int32_t get_p_rew() {
    return rewiring_data.p_rew;
}