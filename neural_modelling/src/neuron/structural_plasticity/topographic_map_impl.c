/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/*! \file
 *
 * SUMMARY
 *  \brief This file contains the main functions for probabilistic
 *  synaptogenesis.
 *
 * Author: Petrut Bogdan
 *
 */
#include <neuron/structural_plasticity/synaptogenesis_dynamics.h>
#include <neuron/population_table/population_table.h>

#include <random.h>
#include <spin1_api.h>
#include <debug.h>
#include <stdfix-full-iso.h>

#include <neuron/synapse_row.h>

#include <neuron/synapses.h>
#include <neuron/plasticity/synapse_dynamics.h>

#include <common/maths-util.h>
#include <neuron/structural_plasticity/sp_structs.h>
#include <simulation.h>

// For last spike selection
#include <circular_buffer.h>

//-----------------------------------------------------------------------------
// External functions                                                         |
//-----------------------------------------------------------------------------

//! How to find a neuron to affect
typedef bool (search_for_neuron_t)(
        uint32_t id, address_t row, structural_plasticity_data_t *sp_data);

//! How to remove a neuron from the network
typedef bool (remove_neuron_t)(
        uint32_t offset, address_t row);

//! How to add a neuron to the network
typedef bool (add_neuron_t)(
        uint32_t id, address_t row, uint32_t weight, uint32_t delay,
        uint32_t type);

//! How to get the size of a particular synaptic matrix row
typedef size_t (number_of_connections_in_row_t)(
        address_t row);

//! The profile of functions
struct access_functions_t {
    search_for_neuron_t *search_for_neuron;
    remove_neuron_t *remove_neuron;
    add_neuron_t *add_neuron;
    number_of_connections_in_row_t *number_of_connections_in_row;
};

static const struct access_functions_t funcs = {
#if STDP_ENABLED == 1
    &find_plastic_neuron_with_id,
    &remove_plastic_neuron_at_offset,
    &add_plastic_neuron_with_id,
    &synapse_row_num_plastic_controls
#else
    &find_static_neuron_with_id,
    &remove_static_neuron_at_offset,
    &add_static_neuron_with_id,
    &synapse_row_num_fixed_synapses
#endif
};

//-----------------------------------------------------------------------------
// Structures and global data                                                 |
//-----------------------------------------------------------------------------
// DMA tags
#define DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING 5
#define DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING 7

#define MAX_SHORT 65535

//! information per atom
typedef struct {
    uint32_t key;
    uint32_t n_atoms;
    uint32_t lo_atom;
    uint32_t mask;
} key_atom_info_t;

// Configuration data
typedef struct {
    uint32_t fast;
    uint32_t p_rew;
    uint32_t weight[2];
    uint32_t delay;
    uint32_t s_max;
    int32_t lateral_inhibition;
    int32_t random_partner;
    uint32_t app_no_atoms;
    uint32_t low_atom;
    uint32_t high_atom;
    uint32_t machine_no_atoms;
    uint32_t grid_x;
    uint32_t grid_y;
    uint32_t p_elim_dep;
    uint32_t p_elim_pot;
    mars_kiss64_seed_t shared_seed;
    mars_kiss64_seed_t local_seed;
    uint32_t n_pre_pops;
    uint32_t data[];
} rewiring_config_t;

typedef struct {
    uint16_t n_pre_vertices;
    uint16_t sp_control;
    uint32_t n_atoms;
    key_atom_info_t key_atom_info[];
} subpop_config_t;

typedef struct {
    uint32_t size;
    uint16_t data[];
} probabilities_t;

//! individual pre-synaptic sub-population information
typedef struct {
    uint16_t no_pre_vertices;
    int16_t sp_control;
    int32_t total_no_atoms;
    key_atom_info_t *key_atom_info;
} subpopulation_info_t;

//! table of individual pre-synaptic information
typedef struct {
    uint32_t no_pre_pops;
    subpopulation_info_t *subpop_info;
} pre_pop_info_table_t;

//! parameters of the synaptic rewiring model
typedef struct {
    uint32_t p_rew, fast, weight[2], delay, s_max, app_no_atoms,
        machine_no_atoms, low_atom, high_atom,
        size_ff_prob, size_lat_prob, grid_x, grid_y, p_elim_dep, p_elim_pot;
    // the 2 seeds that are used: shared for sync, local for everything else
    mars_kiss64_seed_t shared_seed, local_seed;
    // information about all pre-synaptic sub-populations eligible for rewiring
    pre_pop_info_table_t pre_pop_info_table;
    // distance dependent probabilities LUTs
    uint16_t *ff_probabilities, *lat_probabilities;
    // inverse of synaptic matrix
    int32_t *post_to_pre_table;
    // flags for synapse type of lateral connections and whether formations
    // sample randomly from all available neurons
    int32_t lateral_inhibition, random_partner;
} rewiring_data_t;

// the instantiation of the previous struct
static rewiring_data_t rewiring_data;

// dma_buffer defined in spike_processing.h
static dma_buffer rewiring_dma_buffer;

//! struct representing the current state of rewiring
typedef struct {
    // what synaptic row are we servicing?
    address_t sdram_synaptic_row;
    // what are the currently selecting pre- and post-synaptic neurons and
    // what is the distance between them
    uint32_t pre_syn_id, post_syn_id, distance;
    // data structure to pass back weight, delay and offset information from
    // static synapses / stdp synapses
    structural_plasticity_data_t sp_data;
    // what is the current time
    uint32_t current_time;
    // what is the current control word
    int16_t current_controls;
    // what are the global pre- and post-synaptic neuron IDs
    uint32_t global_pre_syn_id, global_post_syn_id;
    // does the post to pre table have contain a connection for the selected
    // slot
    bool element_exists;
    // information extracted from the post to pre table
    uint32_t offset_in_table, pop_index, subpop_index, neuron_index;
    // circular buffer indices
    uint32_t my_cb_input, my_cb_output, no_spike_in_interval, cb_total_size;
    // a local reference to the circular buffer
    circular_buffer cb;
} current_state_t;

// instantiation of the previous struct
static current_state_t state;

#define ANY_SPIKE ((spike_t) -1)

// easy access to the two RNGs
static inline uint32_t random_from_shared(uint32_t limit) {
    return ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) * limit;
}

static inline uint32_t random_from_local(uint32_t limit) {
    return ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) * limit;
}

//! abs function
static int my_abs(int a) {
    return a < 0 ? -a : a;
}

//! function to unpack element from post-to-pre table into constituent bits
static inline bool unpack_post_to_pre(
    int32_t value, uint *pop_index,
    uint *subpop_index, uint *neuron_index)
{
    if (value == -1) {
        return false;
    }
    *neuron_index = (value      ) & 0xFFFF;
    *subpop_index = (value >> 16) & 0xFF;
    *pop_index    = (value >> 24) & 0xFF;
    return true;
}

//! opposite function of unpack. packs up different bits into a word to be
//! placed into the post-to-pre table
static inline int pack(
    uint32_t pop_index, uint32_t subpop_index, uint32_t neuron_index)
{
    uint32_t value, masked_pop_index, masked_subpop_index, masked_neuron_index;
    masked_pop_index    = pop_index    & 0xFF;
    masked_subpop_index = subpop_index & 0xFF;
    masked_neuron_index = neuron_index & 0xFFFF;
    value = (masked_pop_index << 24) |
            (masked_subpop_index << 16) |
             masked_neuron_index;
    return (int) value;
}

//-----------------------------------------------------------------------------
// Initialisation                                                             |
//-----------------------------------------------------------------------------

//! \brief Initialisation of synaptic rewiring (synaptogenesis)
//! parameters (random seed, spread of receptive field etc.)
//! \param[in] sdram_sp_address Address of the start of the SDRAM region
//! which contains synaptic rewiring params.
//! \return address_t Address after the final word read from SDRAM.
address_t synaptogenesis_dynamics_initialise(address_t sdram_sp_address)
{
    log_debug("SR init.");

    log_debug("Registering DMA callback");
    simulation_dma_transfer_done_callback_on(
            DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING,
            synaptic_row_restructure);
    log_debug("Callback registered");

    // Read in all of the parameters from SDRAM
    rewiring_config_t *config = (rewiring_config_t *) sdram_sp_address;
    rewiring_data.fast = config->fast;
    rewiring_data.p_rew = config->p_rew;
    rewiring_data.weight[0] = config->weight[0];
    rewiring_data.weight[1] = config->weight[1];
    rewiring_data.delay = config->delay;
    rewiring_data.s_max = config->s_max;
    rewiring_data.lateral_inhibition = config->lateral_inhibition;
    rewiring_data.random_partner = config->random_partner;

    rewiring_data.app_no_atoms = config->app_no_atoms;
    rewiring_data.low_atom = config->low_atom;
    rewiring_data.high_atom = config->high_atom;
    rewiring_data.machine_no_atoms = config->machine_no_atoms;

    rewiring_data.grid_x = config->grid_x;
    rewiring_data.grid_y = config->grid_y;

    rewiring_data.p_elim_dep = config->p_elim_dep;
    rewiring_data.p_elim_pot = config->p_elim_pot;

    rewiring_data.shared_seed[0] = config->shared_seed[0];
    rewiring_data.shared_seed[1] = config->shared_seed[1];
    rewiring_data.shared_seed[2] = config->shared_seed[2];
    rewiring_data.shared_seed[3] = config->shared_seed[3];

    rewiring_data.local_seed[0] = config->local_seed[0];
    rewiring_data.local_seed[1] = config->local_seed[1];
    rewiring_data.local_seed[2] = config->local_seed[2];
    rewiring_data.local_seed[3] = config->local_seed[3];

    rewiring_data.pre_pop_info_table.no_pre_pops = config->n_pre_pops;

    // Need to malloc space for subpop_info, i.e. an array
    // containing information for each pre-synaptic application vertex
    if (!rewiring_data.pre_pop_info_table.no_pre_pops) {
        return NULL;
    }
    rewiring_data.pre_pop_info_table.subpop_info =
            sark_alloc(rewiring_data.pre_pop_info_table.no_pre_pops,
                    sizeof(subpopulation_info_t));

    void *sp_word = config->data;
    for (uint32_t i = 0; i < rewiring_data.pre_pop_info_table.no_pre_pops; i++) {
        subpopulation_info_t *subpopinfo =
                &rewiring_data.pre_pop_info_table.subpop_info[i];
        subpop_config_t *subpop_config = sp_word;

        // Read the actual number of presynaptic subpopulations
        subpopinfo->no_pre_vertices = subpop_config->n_pre_vertices;
        subpopinfo->sp_control = subpop_config->sp_control;
        subpopinfo->total_no_atoms = subpop_config->n_atoms;
        subpopinfo->key_atom_info =
                sark_alloc(subpopinfo->no_pre_vertices, sizeof(key_atom_info_t));
        for (uint32_t j = 0; j < subpopinfo->no_pre_vertices; j++) {
            subpopinfo->key_atom_info[j] = subpop_config->key_atom_info[j];
        }
        // Advance the config pointer past the inline data
        sp_word = &subpop_config->key_atom_info[subpop_config->n_pre_vertices];
    }

    // Read the probability vs distance tables into DTCM
    probabilities_t *prob_config = sp_word;

    rewiring_data.size_ff_prob = prob_config->size;
    rewiring_data.ff_probabilities =
            sark_alloc(rewiring_data.size_ff_prob, sizeof(uint16_t));
    for (uint32_t i = 0; i < rewiring_data.size_ff_prob; i++) {
        rewiring_data.ff_probabilities[i] = prob_config->data[i];
    }

    // Advance the config pointer past the inline data
    prob_config = (probabilities_t *) &prob_config->data[prob_config->size];

    rewiring_data.size_lat_prob = prob_config->size;
    rewiring_data.lat_probabilities =
            sark_alloc(rewiring_data.size_lat_prob, sizeof(uint16_t));
    for (uint32_t i = 0; i < rewiring_data.size_lat_prob; i++) {
        rewiring_data.lat_probabilities[i] = prob_config->data[i];
    }

    // Advance the config pointer past the inline data
    sp_word = &prob_config->data[prob_config->size];

    // Setting up Post to Pre table
    rewiring_data.post_to_pre_table = sp_word;
    // sanity check
    assert(((int) rewiring_data.post_to_pre_table) % 4 == 4);
    int total_no_of_elements =
            rewiring_data.s_max * rewiring_data.machine_no_atoms;

    // Advance the config pointer past the inline data (to the end)
    sp_word = &rewiring_data.post_to_pre_table[total_no_of_elements + 1];

    // Setting up RNG
    validate_mars_kiss64_seed(rewiring_data.shared_seed);
    // Setting up local RNG
    validate_mars_kiss64_seed(rewiring_data.local_seed);

    // Setting up DMA buffers
    rewiring_dma_buffer.row =
            sark_alloc(10 * rewiring_data.s_max, sizeof(uint32_t));
    if (rewiring_dma_buffer.row == NULL) {
        log_error("Fail init DMA buffers");
        rt_error(RTE_SWERR);
    }

    log_debug("SR init complete.");
    return (address_t) sp_word;
}

//! after a set of rewiring attempts, update the indices in the circular buffer
//! between which we will be looking at the next batch of attempts
void update_goal_posts(uint32_t time) {
    use(time);
    if (!received_any_spike()) {
        state.no_spike_in_interval = 0;
        return;
    }
    state.cb = get_circular_buffer();
    state.cb_total_size = circular_buffer_real_size(state.cb);

    state.my_cb_output = state.my_cb_input;
    state.my_cb_input = circular_buffer_input(state.cb) & state.cb_total_size;

    state.no_spike_in_interval =
            state.my_cb_input >= state.my_cb_output ?
            state.my_cb_input - state.my_cb_output :
            (state.my_cb_input + state.cb_total_size + 1) - state.my_cb_output;
}

//! randomly (with uniform probability) select one of the last received spikes
static inline spike_t select_last_spike(void) {
    if (state.no_spike_in_interval == 0) {
        return ANY_SPIKE;
    }

    uint32_t offset = random_from_local(state.no_spike_in_interval);
    return circular_buffer_value_at_index(
            state.cb, (state.my_cb_output + offset) & state.cb_total_size);
}

//! Compute distances (strictly, the square of the distance)
static inline void compute_distance(uint pre_app_pop, uint pre_sub_pop) {
    // To do this I need to take the DIV and MOD of the postsyn neuron ID,
    // and of the presyn neuron ID. Then I compute the distance with these 2
    // measures

    int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;

    // Pre computation requires querying the table with global information
    pre_global_id = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
            .key_atom_info[pre_sub_pop].lo_atom + state.pre_syn_id;
    post_global_id = state.post_syn_id + rewiring_data.low_atom;

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
    uint delta_x = my_abs(pre_x - post_x);
    uint delta_y = my_abs(pre_y - post_y);

    if (delta_x > rewiring_data.grid_x >> 1 && rewiring_data.grid_x > 1) {
        delta_x -= rewiring_data.grid_x;
    }

    if (delta_y > rewiring_data.grid_y >> 1 && rewiring_data.grid_y > 1) {
        delta_y -= rewiring_data.grid_y;
    }

    // Update the state with what we've found
    state.distance = delta_x * delta_x + delta_y * delta_y;
    state.global_pre_syn_id = pre_global_id;
    state.global_post_syn_id = post_global_id;
}

static inline uint32_t find_index(
        uint choice, subpopulation_info_t *preapppop_info) {
    uint32_t sum = 0;
    uint32_t i = 0;
    for (; i < preapppop_info->no_pre_vertices; i++) {
        sum += preapppop_info->key_atom_info[i].n_atoms;
        if (sum >= choice) {
            break;
        }
    }
    return i;
}

// \brief Unpack a spike into key and identifying information for the neuron.
// \param[in] spike: the spike to be unpacked
// \param[out] pre_app_pop: the unpacked population index
// \param[out] pre_sub_pop: the unpacked index within the population
// \param[out] choice: the remaining masked bits
static inline void unpack_spike_to_neuron(
        spike_t spike, uint *pre_app_pop, uint *pre_sub_pop, uint *choice)
{
    // Identify pop, subpop and lo and hi atoms
    // Amazing linear search inc.
    // Loop over all populations
    for (uint i = 0; i < rewiring_data.pre_pop_info_table.no_pre_pops; i++) {
        subpopulation_info_t *pre_info =
                &rewiring_data.pre_pop_info_table.subpop_info[i];

        // Loop over all subpopulations and check if the KEY matches
        // (with neuron ID masked out)
        for (uint32_t j = 0; j < pre_info->no_pre_vertices; j++) {
            key_atom_info_t *kai = &pre_info->key_atom_info[j];

            if ((spike & kai->mask) == kai->key) {
                *pre_app_pop = i;
                *pre_sub_pop = j;
                *choice = spike & ~kai->mask;
                // return; // TODO: Should we stop at the first match?
            }
        }
    }
}

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] time: the current timestep
//! \return None
void synaptogenesis_dynamics_rewire(uint32_t time)
{
    state.current_time = time;

    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id = random_from_shared(rewiring_data.app_no_atoms);

    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
            post_id > rewiring_data.high_atom) {
        setup_synaptic_dma_read();
        return;
    }
    post_id -= rewiring_data.low_atom;

    // Select an arbitrary synaptic element for the neurons
    uint row_offset = post_id * rewiring_data.s_max;
    uint column_offset = random_from_local(rewiring_data.s_max);
    uint total_offset = row_offset + column_offset;
    int value = rewiring_data.post_to_pre_table[total_offset];
    state.offset_in_table = total_offset;

    uint pre_app_pop = 0, pre_sub_pop = 0, choice = 0;
    bool element_exists =
            unpack_post_to_pre(value, &pre_app_pop, &pre_sub_pop, &choice);

    state.element_exists = element_exists;
    spike_t spike;
    if (element_exists) {
        subpopulation_info_t *preapppop_info =
                &rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop];
        spike = preapppop_info->key_atom_info[pre_sub_pop].key | choice;
    } else if (rewiring_data.random_partner) {
        pre_app_pop = random_from_local(
                rewiring_data.pre_pop_info_table.no_pre_pops);
        subpopulation_info_t *preapppop_info =
                &rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop];

        // Select presynaptic subpopulation
        pre_sub_pop = find_index(
                random_from_local(preapppop_info->total_no_atoms),
                preapppop_info);

        // Select a presynaptic neuron ID
        choice = random_from_local(
                preapppop_info->key_atom_info[pre_sub_pop].n_atoms);
        spike = preapppop_info->key_atom_info[pre_sub_pop].key | choice;
    } else {
        // Retrieve the last spike
        spike = select_last_spike();
        if (spike == ANY_SPIKE) {
            log_debug("No previous spikes");
            setup_synaptic_dma_read();
            return;
        }

        // unpack the spike into key and identifying information for the neuron
        unpack_spike_to_neuron(spike, &pre_app_pop, &pre_sub_pop, &choice);
    }

    address_t synaptic_row_address;
    size_t n_bytes;

    if (!population_table_get_first_address(spike, &synaptic_row_address,
            &n_bytes)) {
        log_error("FAIL@key %d", spike);
        rt_error(RTE_SWERR);
    }

    // Saving current state
    state.pop_index = pre_app_pop;
    state.subpop_index = pre_sub_pop;
    state.neuron_index = choice;
    state.sdram_synaptic_row = synaptic_row_address;
    state.pre_syn_id = choice;
    state.post_syn_id = post_id;
    state.current_controls = rewiring_data.pre_pop_info_table
            .subpop_info[pre_app_pop].sp_control;

    // Compute distances; updates state fields
    compute_distance(pre_app_pop, pre_sub_pop);

    while (!spin1_dma_transfer(
            DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING, synaptic_row_address,
            rewiring_dma_buffer.row, DMA_READ, n_bytes)) {
        log_error("DMA queue full-read");
    }
    rewiring_dma_buffer.n_bytes_transferred = n_bytes;
    rewiring_dma_buffer.sdram_writeback_address = synaptic_row_address;
}

//! \brief This function is a rewiring DMA callback
//! \param[in] dma_id: the ID of the DMA
//! \param[in] dma_tag: the DMA tag, i.e. the tag used for reading row for rew.
//! \return nothing
void synaptic_row_restructure(uint dma_id, uint dma_tag)
{
    // the synaptic row is in rewiring_dma_buffer, while
    // the selected pre- and postsynaptic IDs are in state
    use(dma_id);
    use(dma_tag);

    // find the offset of the neuron in the current row
    bool search_hit = funcs.search_for_neuron(
            state.post_syn_id, rewiring_dma_buffer.row, &state.sp_data);

    if (state.element_exists && search_hit) {
        synaptogenesis_dynamics_elimination_rule();
    } else {
        synaptogenesis_dynamics_formation_rule();
    }
    // service the next event (either rewiring or synaptic)
    setup_synaptic_dma_read();
}

// Trivial helper; has to be macro because uses log_error()
#define DMA_WRITEBACK(msg) \
    do {\
        while (!spin1_dma_transfer(\
                DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING,\
                rewiring_dma_buffer.sdram_writeback_address,\
                rewiring_dma_buffer.row, DMA_WRITE,\
                rewiring_dma_buffer.n_bytes_transferred)) {\
            log_error("%s", msg);\
        }\
    } while (0)

//! \brief Formation and elimination are structurally agnostic, i.e. they don't
//! care how synaptic rows are organised in physical memory.
//!
//!  As such, they need to call functions that have a knowledge of how the
//!  memory is physically organised to be able to modify Plastic-Plastic
//!  synaptic regions.
//!
//!  The elimination rule calls the remove neuron function in the appropriate
//!  module (STDP or static).
//!  \return true if elimination was successful
bool synaptogenesis_dynamics_elimination_rule(void)
{
    // Is synaptic weight <.5 g_max? (i.e. synapse is depressed)
    uint32_t r = mars_kiss64_seed(rewiring_data.local_seed);
    int appr_scaled_weight = rewiring_data.lateral_inhibition ?
            rewiring_data.weight[state.current_controls] :
            rewiring_data.weight[0];
    if (state.sp_data.weight < (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_dep) {
        return false;
    }

    // otherwise, if synapse is potentiated, use probability 2
    if (state.sp_data.weight >= (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_pot) {
        return false;
    }
    if (!funcs.remove_neuron(state.sp_data.offset,
            rewiring_dma_buffer.row)) {
        return false;
    }
    DMA_WRITEBACK("DMA queue full-removal");
    rewiring_data.post_to_pre_table[state.offset_in_table] = -1;
    return true;
}

//! \brief Formation and elimination are structurally agnostic, i.e. they don't
//! care how synaptic rows are organised in physical memory.
//!
//!  As such, they need to call functions that have a knowledge of how the
//!  memory is physically organised to be able to modify Plastic-Plastic
//!  synaptic regions.
//!
//!  The formation rule calls the add neuron function in the appropriate
//!  module (STDP or static).
//!  \return true if formation was successful
bool synaptogenesis_dynamics_formation_rule(void)
{
    // Distance based probability extracted from the appropriate LUT
    uint16_t probability;
    uint no_elems = funcs.number_of_connections_in_row(
            synapse_row_fixed_region(rewiring_dma_buffer.row));
    if (no_elems >= rewiring_data.s_max) {
        log_error("row is full");
        return false;
    }

    if ((state.current_controls == 0 &&
            state.distance > rewiring_data.size_ff_prob)
            || (state.current_controls == 1 &&
            state.distance > rewiring_data.size_lat_prob)) {
        return false;
    }

    if (state.current_controls == 0) {
        probability = rewiring_data.ff_probabilities[state.distance];
    } else {
        probability = rewiring_data.lat_probabilities[state.distance];
    }
    uint16_t r = random_from_local(MAX_SHORT);
    if (r > probability) {
        return false;
    }
    int appr_scaled_weight = rewiring_data.weight[
            rewiring_data.lateral_inhibition ? state.current_controls : 0];

    if (!funcs.add_neuron(state.post_syn_id, rewiring_dma_buffer.row,
            appr_scaled_weight, rewiring_data.delay,
            rewiring_data.lateral_inhibition ? state.current_controls : 0)) {
        return false;
    }
    DMA_WRITEBACK("DMA queue full-formation");

    int the_pack =
            pack(state.pop_index, state.subpop_index, state.neuron_index);
    rewiring_data.post_to_pre_table[state.offset_in_table] = the_pack;
    return true;
}

//! retrieve the period of rewiring
//! based on is_fast(), this can either mean how many times rewiring happens
//! in a timestep, or how many timesteps have to pass until rewiring happens.
int32_t get_p_rew(void) {
    return rewiring_data.p_rew;
}

//! controls whether rewiring is attempted multiple times per timestep
//! or after a number of timesteps.
bool is_fast(void) {
    return rewiring_data.fast == 1;
}
