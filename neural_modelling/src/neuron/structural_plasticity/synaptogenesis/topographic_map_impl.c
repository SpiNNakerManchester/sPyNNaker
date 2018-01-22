/*! \file
 *
 *  \brief This file contains the main functions for topographic map formation,
 *  i.e. probabilistic synaptogenesis.
 *
 */
#include "../synaptogenesis_dynamics.h"
#include "../../population_table/population_table.h"


#include <random.h>
#include <spin1_api.h>
#include <debug.h>
#include <stdfix-full-iso.h>

#include "../../synapse_row.h"

#include "../../synapses.h"
#include "../../plasticity/synapse_dynamics.h"

#include "../../../common/maths-util.h"
#include "../../../common/sp_structs.h"
#include "simulation.h"

// For last spike selection
#include <circular_buffer.h>


//---------------------------------------
// External functions
//---------------------------------------
bool (*search_for_neuron)(uint32_t, address_t, structural_plasticity_data_t *);
bool (*remove_neuron)(uint32_t, address_t);
bool (*add_neuron)(uint32_t, address_t, uint32_t, uint32_t, uint32_t);
int (*number_of_connections_in_row)(address_t);


//---------------------------------------
// Structures and global data
//---------------------------------------
// DMA tags
//#define DMA_TAG_READ_SYNAPTIC_ROW 0
//#define DMA_TAG_WRITE_PLASTIC_REGION 1
#define DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING 5
#define DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING 7
#define KEY_INFO_CONSTANTS 4

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
    uint32_t p_rew, fast, weight[2], delay, s_max, app_no_atoms,
        machine_no_atoms, low_atom, high_atom,\
        size_ff_prob, size_lat_prob, grid_x, grid_y, p_elim_dep, p_elim_pot;
    mars_kiss64_seed_t shared_seed, local_seed;
    pre_pop_info_table_t pre_pop_info_table;
    // distance dependent probabilities LUTs
    uint16_t *ff_probabilities, *lat_probabilities;
    int32_t *post_to_pre_table;
    int32_t lateral_inhibition, random_partner;
} rewiring_data_t;

rewiring_data_t rewiring_data;

// dma_buffer defined in spike_processing.h
dma_buffer rewiring_dma_buffer;

typedef struct {
    address_t sdram_synaptic_row;
    uint32_t pre_syn_id, post_syn_id, distance;
    structural_plasticity_data_t sp_data;
    uint32_t current_time;
    int16_t current_controls;
    uint32_t global_pre_syn_id, global_post_syn_id;
    bool element_exists;
    uint32_t offset_in_table, pop_index, subpop_index, neuron_index;
    // circular buffer indices
    uint32_t my_cb_input, my_cb_output, no_spike_in_interval, cb_total_size;
    circular_buffer cb;
} current_state_t;

current_state_t current_state;


static int my_abs(int a) {
    return a < 0 ? -a : a;
}

static inline bool unpack_post_to_pre(
	int32_t value, uint* pop_index,
	uint* subpop_index, uint* neuron_index) {
    // log_debug("value %d", value);
    if (value == -1) {
        return false;
    }
    *neuron_index = (value    ) & 0xFFFF;
    *subpop_index = (value>>16) & 0xFF;
    *pop_index    = (value>>24) & 0xFF;
    return true;
}

static inline int pack(pop_index, subpop_index, neuron_index) {
    int value, masked_pop_index, masked_subpop_index, masked_neuron_index;
    masked_pop_index    = pop_index    & 0xFF;
    masked_subpop_index = subpop_index & 0xFF;
    masked_neuron_index = neuron_index & 0xFFFF;
    value = (masked_pop_index << 24) |
            (masked_subpop_index << 16) |
             masked_neuron_index;
    return value;
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
    log_debug("SR init.");
    log_debug("Registering DMA callback");
    simulation_dma_transfer_done_callback_on(
	    DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING,
	    synaptic_row_restructure);
    log_debug("Callback registered");
    // Read in all of the parameters from SDRAM
    int32_t *sp_word = (int32_t*) sdram_sp_address;
    rewiring_data.fast = *sp_word++;
    rewiring_data.p_rew = *sp_word++;
    rewiring_data.weight[0] = *sp_word++;
    rewiring_data.weight[1] = *sp_word++;
    rewiring_data.delay = *sp_word++;
    rewiring_data.s_max = *sp_word++;
    rewiring_data.lateral_inhibition = *sp_word++;
    rewiring_data.random_partner = *sp_word++;

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

    rewiring_data.local_seed[0] = *sp_word++;
    rewiring_data.local_seed[1] = *sp_word++;
    rewiring_data.local_seed[2] = *sp_word++;
    rewiring_data.local_seed[3] = *sp_word++;

    rewiring_data.pre_pop_info_table.no_pre_pops = *sp_word++;

    // Need to malloc space for subpop_info, i.e. an array
    // containing information for each pre-synaptic
    // application vertex
    if (rewiring_data.pre_pop_info_table.no_pre_pops==0)
        return NULL;

    rewiring_data.pre_pop_info_table.subpop_info = (subpopulation_info_t*) sark_alloc(
	    rewiring_data.pre_pop_info_table.no_pre_pops, sizeof(subpopulation_info_t));

    uint32_t index;
    uint16_t *half_word;
    for (index = 0;
	    index < rewiring_data.pre_pop_info_table.no_pre_pops;
	    index ++) {
        // Read the actual number of presynaptic subpopulations
        half_word = (uint16_t*) sp_word;
        rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices = *half_word++;
        rewiring_data.pre_pop_info_table.subpop_info[index].sp_control = *half_word++;
        sp_word = (int32_t*) half_word;
        rewiring_data.pre_pop_info_table.subpop_info[index].total_no_atoms = *sp_word++;
        rewiring_data.pre_pop_info_table.subpop_info[index].key_atom_info =
            (int32_t*) sark_alloc(
                KEY_INFO_CONSTANTS *
                rewiring_data.pre_pop_info_table.subpop_info[index]
                    .no_pre_vertices,
                sizeof(int32_t));
        int32_t subpop_index;
        for (subpop_index = 0;
                subpop_index < KEY_INFO_CONSTANTS *
                        rewiring_data.pre_pop_info_table.subpop_info[index].no_pre_vertices;
                subpop_index++) {
            // key
            rewiring_data.pre_pop_info_table.subpop_info[index]
                    .key_atom_info[subpop_index++] = *sp_word++;
            // n_atoms
            rewiring_data.pre_pop_info_table.subpop_info[index]
                    .key_atom_info[subpop_index++] = *sp_word++;
            // lo_atom
            rewiring_data.pre_pop_info_table.subpop_info[index]
                    .key_atom_info[subpop_index++] = *sp_word++;
            // mask
            rewiring_data.pre_pop_info_table.subpop_info[index]
                    .key_atom_info[subpop_index] = *sp_word++;
        }
    }

    // Read the probability vs distance tables into DTCM
    rewiring_data.size_ff_prob = *sp_word++;
    rewiring_data.ff_probabilities = (uint16_t*) sark_alloc(
	    rewiring_data.size_ff_prob, sizeof(uint16_t));
    log_debug("size ff lut %d", rewiring_data.size_ff_prob);
    half_word = (uint16_t*)sp_word;
    for (index = 0; index < rewiring_data.size_ff_prob; index++) {
        rewiring_data.ff_probabilities[index] = *half_word++;
    }

    sp_word = (int32_t*) half_word;
    rewiring_data.size_lat_prob = *sp_word++;

    log_debug("size lat lut %d", rewiring_data.size_lat_prob);
    rewiring_data.lat_probabilities = (uint16_t*) sark_alloc(
	    rewiring_data.size_lat_prob, sizeof(uint16_t));


    half_word = (uint16_t*)sp_word;
    for (index = 0; index < rewiring_data.size_lat_prob; index++) {
        rewiring_data.lat_probabilities[index] = *half_word++;
        log_debug("lat_probabilities %d for index %d",
        	rewiring_data.lat_probabilities[index], index);
    }

    assert(((int)half_word)%4==4);

    sp_word = (int32_t*) half_word;
    // Setting up Post to Pre table
    rewiring_data.post_to_pre_table = sp_word;
    // log_debug("post to pre %x", rewiring_data.post_to_pre_table);
    int total_no_of_elements = rewiring_data.s_max *
        rewiring_data.machine_no_atoms;
    sp_word = &rewiring_data.post_to_pre_table[total_no_of_elements + 1];

    // Setting up RNG
    validate_mars_kiss64_seed(rewiring_data.shared_seed);
    // Setting up local RNG
    validate_mars_kiss64_seed(rewiring_data.local_seed);

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

    log_debug("SR init complete.");
    return (address_t)sp_word;
}

void update_goal_posts(uint32_t time) {
    use(time);
    if (!received_any_spike()) {
        return;
    }
    current_state.cb = get_circular_buffer();
    current_state.cb_total_size = circular_buffer_real_size(current_state.cb);

    current_state.my_cb_output = current_state.my_cb_input;
    current_state.my_cb_input = (
	    circular_buffer_input(current_state.cb)) & current_state.cb_total_size;

     current_state.no_spike_in_interval = (
	    current_state.my_cb_input >= current_state.my_cb_output
	    ? current_state.my_cb_input - current_state.my_cb_output
	    : (current_state.my_cb_input + current_state.cb_total_size + 1) -
		    current_state.my_cb_output);
}

static inline spike_t select_last_spike () {
    if (current_state.no_spike_in_interval == 0)
        return -1;
    uint32_t offset=ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
	    current_state.no_spike_in_interval;
    return circular_buffer_value_at_index(
	    current_state.cb,
	    (current_state.my_cb_output + offset) & current_state.cb_total_size);
}


//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] None
//! \return None
void synaptogenesis_dynamics_rewire(uint32_t time) {
    current_state.current_time = time;
    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id;
    post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) *
	    rewiring_data.app_no_atoms;
    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
	    post_id > rewiring_data.high_atom) {
        log_debug("\t| NOTME %d @ %d", post_id, time);
        _setup_synaptic_dma_read();
        return;
    }
    post_id -= rewiring_data.low_atom;

    uint pre_app_pop, pre_sub_pop, choice;
    bool element_exists=false;

    // Select an arbitrary synaptic element for the neurons
    uint row_offset, column_offset;
    row_offset = post_id * rewiring_data.s_max;
    column_offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
	    rewiring_data.s_max;
    uint total_offset = (row_offset + column_offset);
    int value = rewiring_data.post_to_pre_table[total_offset];
    current_state.offset_in_table = total_offset;

    element_exists = unpack_post_to_pre(value, &pre_app_pop,
	    &pre_sub_pop, &choice);

    current_state.element_exists = element_exists;
    spike_t _spike = -1;
    if (!element_exists && !rewiring_data.random_partner) {
        // Retrieve the last spike
        if (received_any_spike()) {
            _spike = select_last_spike();
//              _spike = get_last_spike();
        }
        //    log_debug("spike key %d", _spike);
        if (_spike == -1) {
            log_debug("No previous spikes");
            _setup_synaptic_dma_read();
            return;
        }

        // unpack the spike into key and identifying information for the neuron
        // Identify pop, subpop and lo and hi atoms
        // Amazing linear search inc.
        // Loop over all populations
        bool found=false;
        for (int i=0; i< rewiring_data.pre_pop_info_table.no_pre_pops; i++) {
            // Loop over all subpopulations and check if the KEY matches
            // (with neuron id masked out)
            for (int subpop_index = 0;
        	    subpop_index < rewiring_data.pre_pop_info_table.subpop_info[i].no_pre_vertices;
        	    subpop_index++) {
                if ((_spike & rewiring_data
                	.pre_pop_info_table.subpop_info[i]
                        .key_atom_info[KEY_INFO_CONSTANTS * subpop_index + 3])
                	== rewiring_data.pre_pop_info_table.subpop_info[i]
			        .key_atom_info[KEY_INFO_CONSTANTS * subpop_index]) {
                    pre_app_pop = i;
                    pre_sub_pop = subpop_index;
                    choice = _spike &
                	    ~rewiring_data.pre_pop_info_table.subpop_info[i]
                            .key_atom_info[KEY_INFO_CONSTANTS * subpop_index + 3];
                    found = true;
                }
            }
        }
    } else if (!element_exists && rewiring_data.random_partner) {
	pre_app_pop = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
        	    * rewiring_data.pre_pop_info_table.no_pre_pops;
	// Select presynaptic subpopulation
	choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
        	    * rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].total_no_atoms;
	uint32_t sum=0;
	int i;
	for (i=0;
		i<rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop].no_pre_vertices;
		i++) {
	    sum += rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
		    .key_atom_info[KEY_INFO_CONSTANTS * i + 1];
	    if (sum >= choice) {
		break;
	    }
	}
	pre_sub_pop = i;
	// Select a presynaptic neuron id
	choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
		rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
                .key_atom_info[KEY_INFO_CONSTANTS * pre_sub_pop + 1];
	// Log all random stuff
	// population_table_get_first_address() returns the address
	// (in SDRAM) of the selected synaptic row
	_spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
		.key_atom_info[pre_sub_pop * KEY_INFO_CONSTANTS + 0] | choice;
    } else {
        _spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
                .key_atom_info[pre_sub_pop * KEY_INFO_CONSTANTS + 0] | choice;
    }



    address_t synaptic_row_address;
    size_t n_bytes;

    if (!population_table_get_first_address(_spike, &synaptic_row_address,
	    &n_bytes)) {
        log_error("FAIL@key %d", _spike);
        rt_error(RTE_SWERR);
    }
    // Saving current state

    current_state.pop_index = pre_app_pop;
    current_state.subpop_index = pre_sub_pop;
    current_state.neuron_index = choice;
    current_state.sdram_synaptic_row = synaptic_row_address;
    current_state.pre_syn_id = choice;
    current_state.post_syn_id = post_id;
    current_state.current_controls = rewiring_data.pre_pop_info_table
        .subpop_info[pre_app_pop].sp_control;


    // Compute distances
    // To do this I need to take the DIV and MOD of the
    // postsyn neuron id, of the presyn neuron id
    // Compute the distance of these 2 measures
    int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;
    // Pre computation requires querying the table with global information
    pre_global_id = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
        .key_atom_info[KEY_INFO_CONSTANTS * pre_sub_pop + 2] +
        current_state.pre_syn_id;
    post_global_id = current_state.post_syn_id + rewiring_data.low_atom;

    if (rewiring_data.grid_x > 1) {
        pre_x = pre_global_id / rewiring_data.grid_x;
        post_x = post_global_id / rewiring_data.grid_x;
    } else {
        pre_x = 0;
        post_x = 0;
    }

    if (rewiring_data.grid_y > 1) {
        pre_y = pre_global_id % rewiring_data.grid_y;
        post_y = post_global_id % rewiring_data.grid_y;
    } else {
        pre_y = 0;
        post_y = 0;
    }


    // With periodic boundary conditions
    uint delta_x, delta_y;
    delta_x = my_abs(pre_x - post_x);
    delta_y = my_abs(pre_y - post_y);

    if( delta_x > rewiring_data.grid_x>>1 && rewiring_data.grid_x > 1)
        delta_x -= rewiring_data.grid_x;

    if( delta_y > rewiring_data.grid_y>>1 && rewiring_data.grid_y > 1)
        delta_y -= rewiring_data.grid_y;

    current_state.distance = delta_x * delta_x + delta_y * delta_y;
    current_state.global_pre_syn_id = pre_global_id;
    current_state.global_post_syn_id = post_global_id;

    /*ad*/log_debug("g_pre_id %d g_post_id %d g_distance_sq %d exists %d %d",
	    pre_global_id, post_global_id, current_state.distance,
	    element_exists, current_state.current_controls);
    log_debug("pre_x %d pre_y %d", pre_x, pre_y);
    log_debug("post_x %d post_y %d", post_x, post_y);

    while (0 == spin1_dma_transfer(
            DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING, synaptic_row_address,
            rewiring_dma_buffer.row, DMA_READ,
            n_bytes)) {
        log_error("DMA queue full-read");
    }
    rewiring_dma_buffer.n_bytes_transferred = n_bytes;
    rewiring_dma_buffer.sdram_writeback_address = synaptic_row_address;
}


// Might need a function for rewiring. One to be called by the timer to
// generate a fake spike and trigger a dma callback
// and one to be called by the dma callback and then call formation or
// elimination
void synaptic_row_restructure(uint dma_id, uint dma_tag) {
    // If I am here, then the DMA read was successful.
    // As such, the synaptic row is in rewiring_dma_buffer, while
    // the selected pre and postsynaptic ids are in current_state

    use(dma_id);
    use(dma_tag);

    log_debug("rew current_weight %d", current_state.sp_data.weight);
    log_debug("sanity check delay %d", current_state.sp_data.delay);

    /*ad*/log_debug("sr_attempt %d %d exists %d",
        current_state.current_time,
        current_state.current_controls,
        current_state.element_exists);

    bool search_hit = search_for_neuron(
	    current_state.post_syn_id,
	    rewiring_dma_buffer.row,
	    &(current_state.sp_data));

    if (current_state.element_exists && search_hit) {
        synaptogenesis_dynamics_elimination_rule();
    } else if (current_state.element_exists && (!search_hit)) {
        log_error("FAIL Search");
        rewiring_data.post_to_pre_table[current_state.offset_in_table] = -1;
        // rt_error(RTE_SWERR);
    } else {
        synaptogenesis_dynamics_formation_rule();
    }
    // This calls _setup_synaptic_dma_read() again!
    _setup_synaptic_dma_read();
}

 /*
    Formation and elimination are structurally agnostic, i.e. they don't
    care how
    synaptic rows are organised in physical memory.

    As such, they need to call functions that have a knowledge of how the
    memory is
    physically organised to be able to modify Plastic-Plastic synaptic regions.
 */
bool synaptogenesis_dynamics_elimination_rule(void) {
    // Is synaptic weight <.5 g_max?
    uint32_t r = mars_kiss64_seed(rewiring_data.local_seed);
    log_debug("elim_prob r %u ctrl %d", r, current_state.current_controls);
    int appr_scaled_weight = rewiring_data.lateral_inhibition ?
        rewiring_data.weight[current_state.current_controls] :
        rewiring_data.weight[0];
    if (current_state.sp_data.weight < (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_dep) {
        log_debug("\t| FAIL DEP %d", current_state.current_time);
        return false;
    }
    // otherwise use probability 2
    if (current_state.sp_data.weight >= (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_pot) {
        log_debug("\t| FAIL POT %d", current_state.current_time);
        return false;
    }
    if (remove_neuron(current_state.sp_data.offset, rewiring_dma_buffer.row)) {
        while (0 == spin1_dma_transfer(
                DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING,
                rewiring_dma_buffer.sdram_writeback_address,
                rewiring_dma_buffer.row, DMA_WRITE,
                rewiring_dma_buffer.n_bytes_transferred)){
            log_error("DMA queue full-removal");
        }
        /*ad*/log_debug("\t| RM pre %d post %d # elems %d rec_conn %d @ %d",
            current_state.global_pre_syn_id,
            current_state.global_post_syn_id,
            number_of_connections_in_row(
            synapse_row_fixed_region(rewiring_dma_buffer.row)),
            current_state.current_controls,
            current_state.current_time);
        rewiring_data.post_to_pre_table[current_state.offset_in_table] = -1;
        return true;
    }
    return false;
}

bool synaptogenesis_dynamics_formation_rule(void) {
    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;
    uint no_elems = number_of_connections_in_row(
        synapse_row_fixed_region(rewiring_dma_buffer.row));
    if (no_elems >= rewiring_data.s_max) {
        log_error("row is full");
        return false;
    }

    if ((current_state.current_controls == 0 &&
	    current_state.distance > rewiring_data.size_ff_prob)
	    || (current_state.current_controls == 1 &&
		    current_state.distance > rewiring_data.size_lat_prob)) {
        /*ad*/log_debug("\t| OOB %d %d %d",
        	current_state.distance,
		current_state.current_time,
		current_state.current_controls);
        return false;
    }
    if (current_state.current_controls == 0) {
        probability = rewiring_data.ff_probabilities[current_state.distance];
    } else {
        probability = rewiring_data.lat_probabilities[current_state.distance];
    }
    uint16_t r =
        ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * MAX_SHORT;
    if (r > probability) {
        log_debug("\t| NO FORM %d", current_state.current_time);
        return false;
    }
    int appr_scaled_weight = rewiring_data.lateral_inhibition ?
        rewiring_data.weight[current_state.current_controls] :
        rewiring_data.weight[0];

    if (add_neuron(current_state.post_syn_id, rewiring_dma_buffer.row,
            appr_scaled_weight, rewiring_data.delay,
            rewiring_data.lateral_inhibition ?
            current_state.current_controls : 0)){

        while (0 == spin1_dma_transfer(
                DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING,
                rewiring_dma_buffer.sdram_writeback_address,
                rewiring_dma_buffer.row, DMA_WRITE,
                rewiring_dma_buffer.n_bytes_transferred)) {
            log_error("DMA queue full-formation");
        }

        /*ad*/log_debug(
        	"\t| FORM pre %d post %d # elems %d dist %d rec_conn %d @ %d",
		current_state.global_pre_syn_id,
		current_state.global_post_syn_id,
		number_of_connections_in_row(
			synapse_row_fixed_region(rewiring_dma_buffer.row)),
		current_state.distance,
		current_state.current_controls,
		current_state.current_time);
        int the_pack = pack(current_state.pop_index,
        	current_state.subpop_index,
		current_state.neuron_index);
        rewiring_data.post_to_pre_table[current_state.offset_in_table] = \
            the_pack;
        return true;
    }
    return false;
}


int32_t get_p_rew(void) {
    return rewiring_data.p_rew;
}

bool is_fast(void) {
    return rewiring_data.fast == 1;
}
