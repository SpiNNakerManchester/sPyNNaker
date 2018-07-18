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
// Static functions                                                           |
//-----------------------------------------------------------------------------
typedef bool (*search_for_neuron_t)
    (uint32_t, address_t, structural_plasticity_data_t *);
typedef bool (*remove_neuron_t)(uint32_t, address_t);
typedef bool (*add_neuron_t)
    (uint32_t, address_t, uint32_t, uint32_t, uint32_t);
typedef size_t (*number_of_connections_in_row_t)(address_t);

#if STDP_ENABLED == 1
static const search_for_neuron_t search_for_neuron =
    &find_plastic_neuron_with_id;
static const remove_neuron_t remove_neuron = &remove_plastic_neuron_at_offset;
static const add_neuron_t add_neuron = &add_plastic_neuron_with_id;
static const number_of_connections_in_row_t number_of_connections_in_row =
    &synapse_row_num_plastic_controls;
#else
static const search_for_neuron_t search_for_neuron =
    &find_static_neuron_with_id;
static const remove_neuron_t remove_neuron = &remove_static_neuron_at_offset;
static const add_neuron_t add_neuron = &add_static_neuron_with_id;
static const number_of_connections_in_row_t number_of_connections_in_row =
    &synapse_row_num_fixed_synapses;
#endif

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

//! individual pre-synaptic sub-population information
typedef struct {
    int16_t no_pre_vertices, sp_control, connection_type;
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

// the instantiation of the previous truct
rewiring_data_t rewiring_data;

// dma_buffer defined in spike_processing.h
dma_buffer rewiring_dma_buffer;

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
    int32_t connection_type;
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
current_state_t current_state;

#define ANY_SPIKE ((spike_t) -1)

//! abs function
static int my_abs(int a) {
    return a < 0 ? -a : a;
}

//! function to unpack elment from post ot pre table into constituent bits
static inline bool unpack_post_to_pre(
    int32_t value, uint* pop_index,
    uint* subpop_index, uint* neuron_index)
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
//! placed into the post to pre table
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
    log_info("SR init.");
    log_debug("Registering DMA callback");
    simulation_dma_transfer_done_callback_on(
        DMA_TAG_READ_SYNAPTIC_ROW_FOR_REWIRING,
        synaptic_row_restructure);
    log_debug("Callback registered");
    // Read in all of the parameters from SDRAM
    int32_t *sp_word = (int32_t *) sdram_sp_address;
    rewiring_data.fast = *sp_word++;
    rewiring_data.p_rew = *sp_word++;
    rewiring_data.weight[0] = *sp_word++;
    rewiring_data.weight[1] = *sp_word++;

    log_info("w[%d, %d]",rewiring_data.weight[0],rewiring_data.weight[1]);

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
    // containing information for each pre-synaptic application vertex
    if (!rewiring_data.pre_pop_info_table.no_pre_pops) {
        return NULL;
    }
    rewiring_data.pre_pop_info_table.subpop_info = sark_alloc(
        rewiring_data.pre_pop_info_table.no_pre_pops,
        sizeof(subpopulation_info_t));

    uint32_t index;
    uint16_t *half_word;
    for (index = 0;
        index < rewiring_data.pre_pop_info_table.no_pre_pops;
        index ++) {
    subpopulation_info_t *subpopinfo =
        &rewiring_data.pre_pop_info_table.subpop_info[index];

        // Read the actual number of presynaptic subpopulations
        half_word = (uint16_t *) sp_word;
        subpopinfo->no_pre_vertices = *half_word++;
        subpopinfo->sp_control = *half_word++;
        sp_word = (int32_t *) half_word;
        subpopinfo->connection_type = *sp_word++;
        log_info("syn_type %d", subpopinfo->connection_type);
        subpopinfo->total_no_atoms = *sp_word++;
        subpopinfo->key_atom_info = sark_alloc(
            subpopinfo->no_pre_vertices, sizeof(key_atom_info_t));
        int32_t subpop_index;
        for (subpop_index = 0;
                subpop_index < subpopinfo->no_pre_vertices;
                subpop_index++) {
            // key
            subpopinfo->key_atom_info[subpop_index].key = *sp_word++;
            // n_atoms
            subpopinfo->key_atom_info[subpop_index].n_atoms = *sp_word++;
            // lo_atom
            subpopinfo->key_atom_info[subpop_index].lo_atom = *sp_word++;
            // mask
            subpopinfo->key_atom_info[subpop_index].mask = *sp_word++;
        }
    }

    // Read the probability vs distance tables into DTCM
    rewiring_data.size_ff_prob = *sp_word++;
    rewiring_data.ff_probabilities = sark_alloc(
        rewiring_data.size_ff_prob, sizeof(uint16_t));
    half_word = (uint16_t *) sp_word;
    for (index = 0; index < rewiring_data.size_ff_prob; index++) {
        rewiring_data.ff_probabilities[index] = *half_word++;
    }

    sp_word = (int32_t *) half_word;
    rewiring_data.size_lat_prob = *sp_word++;

    rewiring_data.lat_probabilities = sark_alloc(
        rewiring_data.size_lat_prob, sizeof(uint16_t));

    half_word = (uint16_t *) sp_word;
    for (index = 0; index < rewiring_data.size_lat_prob; index++) {
        rewiring_data.lat_probabilities[index] = *half_word++;
    }

    assert(((int) half_word) % 4 == 4);

    sp_word = (int32_t *) half_word;

    // Setting up Post to Pre table
    rewiring_data.post_to_pre_table = sp_word;
    int total_no_of_elements = rewiring_data.s_max *
        rewiring_data.machine_no_atoms;
    sp_word = &rewiring_data.post_to_pre_table[total_no_of_elements + 1];

    // Setting up RNG
    validate_mars_kiss64_seed(rewiring_data.shared_seed);
    // Setting up local RNG
    validate_mars_kiss64_seed(rewiring_data.local_seed);

    // Setting up DMA buffers
    rewiring_dma_buffer.row = sark_alloc(
            10 * rewiring_data.s_max, sizeof(uint32_t));
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
        return;
    }
    current_state.cb = get_circular_buffer();
    current_state.cb_total_size = circular_buffer_real_size(current_state.cb);

    current_state.my_cb_output = current_state.my_cb_input;
    current_state.my_cb_input = (
        circular_buffer_input(current_state.cb)
        & current_state.cb_total_size);

    current_state.no_spike_in_interval = (
        current_state.my_cb_input >= current_state.my_cb_output
        ? current_state.my_cb_input - current_state.my_cb_output
        : (current_state.my_cb_input + current_state.cb_total_size + 1) -
            current_state.my_cb_output);
}

//! randomly (with uniform probability) select one of the last received spikes
static inline spike_t select_last_spike(void) {
    if (current_state.no_spike_in_interval == 0) {
        return ANY_SPIKE;
    }
    uint32_t offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        current_state.no_spike_in_interval;
    return circular_buffer_value_at_index(
        current_state.cb,
        (current_state.my_cb_output + offset) & current_state.cb_total_size);
}

//! \brief Function called (usually on a timer from c_main) to
//! trigger the process of synaptic rewiring
//! \param[in] time: the current timestep
//! \return None
void synaptogenesis_dynamics_rewire(uint32_t time)
{
    current_state.current_time = time;

    // Randomly choose a postsynaptic (application neuron)
    uint32_t post_id;
    post_id = ulrbits(mars_kiss64_seed(rewiring_data.shared_seed)) *
        rewiring_data.app_no_atoms;

    // Check if neuron is in the current machine vertex
    if (post_id < rewiring_data.low_atom ||
        post_id > rewiring_data.high_atom) {
        _setup_synaptic_dma_read();
        return;
    }
    post_id -= rewiring_data.low_atom;

    uint pre_app_pop = 0, pre_sub_pop = 0, choice = 0;
    bool element_exists = false;

    // Select an arbitrary synaptic element for the neurons
    uint row_offset, column_offset;
    row_offset = post_id * rewiring_data.s_max;
    column_offset = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        rewiring_data.s_max;
    uint total_offset = row_offset + column_offset;
    int value = rewiring_data.post_to_pre_table[total_offset];
    current_state.offset_in_table = total_offset;

    element_exists = unpack_post_to_pre(value, &pre_app_pop,
        &pre_sub_pop, &choice);

    current_state.element_exists = element_exists;
    spike_t _spike = ANY_SPIKE;
    if (!element_exists && !rewiring_data.random_partner) {
        // Retrieve the last spike
        if (received_any_spike()) {
            _spike = select_last_spike();
        }
        if (_spike == ANY_SPIKE) {
            log_debug("No previous spikes");
            _setup_synaptic_dma_read();
            return;
        }

        // unpack the spike into key and identifying information for the neuron
        // Identify pop, subpop and lo and hi atoms
        // Amazing linear search inc.
        // Loop over all populations
        for (uint i=0; i< rewiring_data.pre_pop_info_table.no_pre_pops; i++) {
        subpopulation_info_t *preapppop_info =
            &rewiring_data.pre_pop_info_table.subpop_info[i];

            // Loop over all subpopulations and check if the KEY matches
            // (with neuron ID masked out)
            for (int subpop_index = 0;
                subpop_index < preapppop_info->no_pre_vertices;
                subpop_index++) {
            key_atom_info_t *kai =
                &preapppop_info->key_atom_info[subpop_index];
                if ((_spike & kai->mask) == kai->key) {
                    pre_app_pop = i;
                    pre_sub_pop = subpop_index;
                    choice = _spike & ~kai->mask;
                }
            }
        }
    } else if (!element_exists && rewiring_data.random_partner) {
    pre_app_pop = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
                * rewiring_data.pre_pop_info_table.no_pre_pops;
    subpopulation_info_t *preapppop_info =
        &rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop];

    // Select presynaptic subpopulation
    choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed))
                * preapppop_info->total_no_atoms;
    uint32_t sum = 0;
    int i;
    for (i=0; i < preapppop_info->no_pre_vertices; i++) {
        sum += preapppop_info->key_atom_info[i].n_atoms;
        if (sum >= choice) {
        break;
        }
    }
    pre_sub_pop = i;

    // Select a presynaptic neuron ID
    choice = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
        preapppop_info->key_atom_info[pre_sub_pop].n_atoms;

    _spike = preapppop_info->key_atom_info[pre_sub_pop].key | choice;
    } else {
        _spike = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
                .key_atom_info[pre_sub_pop].key | choice;
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
    current_state.connection_type = rewiring_data.pre_pop_info_table
            .subpop_info[pre_app_pop].connection_type;

    // Compute distances
    // To do this I need to take the DIV and MOD of the
    // postsyn neuron ID, of the presyn neuron ID
    // Compute the distance of these 2 measures
    int32_t pre_x, pre_y, post_x, post_y, pre_global_id, post_global_id;
    // Pre computation requires querying the table with global information
    pre_global_id = rewiring_data.pre_pop_info_table.subpop_info[pre_app_pop]
            .key_atom_info[pre_sub_pop].lo_atom + current_state.pre_syn_id;
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

    if (delta_x > rewiring_data.grid_x >> 1 && rewiring_data.grid_x > 1) {
        delta_x -= rewiring_data.grid_x;
    }

    if (delta_y > rewiring_data.grid_y >> 1 && rewiring_data.grid_y > 1) {
        delta_y -= rewiring_data.grid_y;
    }

    current_state.distance = delta_x * delta_x + delta_y * delta_y;
    current_state.global_pre_syn_id = pre_global_id;
    current_state.global_post_syn_id = post_global_id;

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
    // the selected pre- and postsynaptic IDs are in current_state
    use(dma_id);
    use(dma_tag);

    // find the offset of the neuron in the current row
    bool search_hit = search_for_neuron(
        current_state.post_syn_id, rewiring_dma_buffer.row,
        &(current_state.sp_data));

    if (current_state.element_exists && search_hit) {
        synaptogenesis_dynamics_elimination_rule();
    } else {
        synaptogenesis_dynamics_formation_rule();
    }
    // service the next event (either rewiring or synaptic)
    _setup_synaptic_dma_read();
}

// Trivial helper; has to be macro because uses log_error()
#define DMA_WRITEBACK(msg) \
    do {\
        while (!spin1_dma_transfer(\
            DMA_TAG_WRITE_SYNAPTIC_ROW_AFTER_REWIRING,\
            rewiring_dma_buffer.sdram_writeback_address,\
            rewiring_dma_buffer.row, DMA_WRITE,\
            rewiring_dma_buffer.n_bytes_transferred)) {\
        log_error(msg);\
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
    int appr_scaled_weight = rewiring_data.weight[current_state.connection_type];
    if (current_state.sp_data.weight < (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_dep) {
        return false;
    }

    // otherwise, if synapse is potentiated, use probability 2
    if (current_state.sp_data.weight >= (appr_scaled_weight / 2) &&
            r > rewiring_data.p_elim_pot) {
        return false;
    }
    if (!remove_neuron(current_state.sp_data.offset,
            rewiring_dma_buffer.row)) {
        return false;
    }
    DMA_WRITEBACK("DMA queue full-removal");
    rewiring_data.post_to_pre_table[current_state.offset_in_table] = -1;
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
        return false;
    }

    if (current_state.current_controls == 0) {
        probability = rewiring_data.ff_probabilities[current_state.distance];
    } else {
        probability = rewiring_data.lat_probabilities[current_state.distance];
    }
    uint16_t r = ulrbits(mars_kiss64_seed(rewiring_data.local_seed)) *
            MAX_SHORT;
    if (r > probability) {
        return false;
    }
    int appr_scaled_weight = rewiring_data.weight[current_state.connection_type];

    if (!add_neuron(current_state.post_syn_id, rewiring_dma_buffer.row,
            appr_scaled_weight, rewiring_data.delay,
            current_state.connection_type)) {
        return false;
    }
    DMA_WRITEBACK("DMA queue full-formation");

    int the_pack = pack(current_state.pop_index,
        current_state.subpop_index,
        current_state.neuron_index);
    rewiring_data.post_to_pre_table[current_state.offset_in_table] = the_pack;
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
