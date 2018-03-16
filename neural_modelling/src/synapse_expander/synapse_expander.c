#include "synapse_expander.h"
#include "matrix_generator.h"
#include "connection_generator.h"
#include "param_generator.h"
#include "rng.h"

#include <stdbool.h>
#include <spin1_api.h>
#include <data_specification.h>
#include <debug.h>

//#define DEBUG_MESSAGES
#define SARK_HEAP 1

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
#define SDRAM_TAG          140
#define MESSAGES_SDRAM_TAG 200
#define ID_DELAY_SDRAM_TAG 180
#define CLEAR_MEMORY_FLAG 0x55555555
#define SLEEP_TIME 10311

#define MAX_PRE_DELAY_ENTRIES 100 // memory limits this
//#define MAX_PRE_DELAY_ENTRIES 150 // memory limits this
//#define MAX_PRE_DELAY_ENTRIES 256 // memory limits this
#define MAX_MEMORY_RETRIES 0
//#define SDRAM_LOCK ALLOC_LOCK
#define SDRAM_LOCK ALLOC_ID

//TODO*** define this somewhere else!
#define BUILD_IN_MACHINE_PORT 1
#define BUILD_IN_MACHINE_TAG  111
#define MAX_N_DELAYS_PER_PACKET 100 // memory limits this
#define MAX_RETRIES 20
//TODO-END

#define PBITS    6
#define XYBITS   ((32 - PBITS)/2)
#define XSHIFT   (PBITS+XYBITS)
#define YSHIFT   (PBITS)
#define XYMASK   ((1 << XYBITS) - 1)
#define PMASK    ((1 <<  PBITS) - 1)
#define _unused(x) ((void)(x))
#define _place_x(place) ((place >> XSHIFT) & XYMASK)
#define _place_y(place) ((place >> YSHIFT) & XYMASK)
#define _place_xy_16(place) (((_place_x(place) & ((1 << 8) - 1)) << 8 )|\
                              (_place_y(place) & ((1 << 8) - 1)))
#define _place_p(placement) ((placement) & PMASK)
#define _preid_delay_i(pd) (pd & 0xFF )
#define _preid_delay_d(pd) ((pd >> 8) & 0xFF)

static bool delay_response_received = false;
static sdp_msg_t delay_message;

uint16_t *pre_delay_pairs = NULL;

matrix_generator_t matrix_generator;
connection_generator_t connection_generator;
param_generator_t weight_generator;
param_generator_t delay_generator;

uint32_t *sdram_address = NULL;

static void handle_sdp_message(uint mailbox, uint sdp_port) {
    use(mailbox);
    use(sdp_port);
    log_info("\t\tACK received");
    delay_response_received = true;
}

static void wait_for_delay_response(uint32_t rand_num) {
//  spin1_delay_us(SLEEP_TIME);
  int retry_count = 0;
  // Wait until the response to the last message has been received
  log_info("\t - Waiting for ACK");
  while (!delay_response_received) {
    if (retry_count >= MAX_RETRIES){
//      rt_error(RTE_ABORT);
      delay_response_received = true;
  //   spin1_exit(0); //error!!!
      break;
    }

  //   Wait for a time for a response
  //   log_info("Waiting for response from last delay message");
    uint32_t shift = (spin1_get_core_id()*spin1_get_chip_id() + retry_count)%28;
    spin1_delay_us(SLEEP_TIME + 2*((rand_num >> shift) & 3) +
                  ((rand_num >> (shift+2)) & 3));

     // Re-send the message
    if (!delay_response_received) {
      spin1_send_sdp_msg(&delay_message, 1);
      retry_count++;
    }
  }

  log_info("\t\t - Waited %u times", retry_count);
}

static void send_n_delays(uint32_t placement, uint16_t *delays, uint32_t n_delays,
                          const uint32_t rand_num, const uint32_t pre_slice_start){

  uint16_t delay_chip = (uint16_t)_place_xy_16(placement);
  uint8_t delay_core  = (uint8_t)_place_p(placement);
  log_info("send_n_delays to 0x%04x.%02u, N = %u",
      delay_chip, delay_core, n_delays);

  // initialise SDP header
  uint8_t src_port = 1;
  delay_message.tag = BUILD_IN_MACHINE_TAG;
  delay_message.flags = 0x07;
  delay_message.dest_addr = delay_chip;
  delay_message.dest_port = (BUILD_IN_MACHINE_PORT << PORT_SHIFT) | delay_core;
  delay_message.srce_addr = spin1_get_chip_id();
  delay_message.srce_port = (src_port << PORT_SHIFT) | spin1_get_core_id();

  if(n_delays == 0){
      uint16_t *data = &delay_message.cmd_rc;
      data[0] = 0;

      delay_message.length = sizeof(sdp_hdr_t) + sizeof(uint16_t);
  }
  else{
    uint16_t *data = &delay_message.cmd_rc;
    data[0] = n_delays;
    data[1] = pre_slice_start;
    spin1_memcpy(&(data[2]), delays, sizeof(uint16_t) * n_delays);

    delay_message.length = sizeof(sdp_hdr_t) + 2*sizeof(uint16_t) +
                           (sizeof(uint16_t) * n_delays);
  }


  spin1_delay_us(1 + ((rand_num >> spin1_get_core_id()) & 3));
  delay_response_received = false;
  spin1_send_sdp_msg(&delay_message, 1);
  wait_for_delay_response(rand_num);

}

// Sends delays to the delay core
static bool send_delays(
        const uint32_t num_placements, const uint32_t *placements,
        const uint32_t *delay_starts, const uint32_t *delay_counts,
        uint16_t n_delays, uint16_t *delays, uint32_t pre_slice_start,
        rng_t rng) {

    uint32_t rand_num = rng_generator(rng);

    if (n_delays == 0) {
        return true;
    }

    log_info("In send delays");

    uint16_t pairs_per_core[MAX_N_DELAYS_PER_PACKET];

    uint32_t starts[num_placements];
    for (uint32_t i = 0; i < num_placements; i++) {
        starts[i] = 0;
    }

    uint16_t seen[num_placements];
    for (uint32_t i = 0; i < num_placements; i++) {
        seen[i] = 0;
    }

    uint16_t prev_pre = 333; // big number so it can't be generated from tools
    uint16_t prev_dly = 333; // again, too big a delay
    uint16_t index = 0;
    uint16_t index_seen = 0;
    uint16_t count = 0;
    uint16_t delay = 0;
    uint16_t delay_end = 0;
    uint32_t place_idx = 0;

    //TODO: Memory was running low so this ended-up overly complicated
    // Find placement for first id/delay pair
    index = pre_slice_start + _preid_delay_i(delays[0]);
    for (uint32_t i = 0; i < num_placements; i++) {
        uint32_t end = delay_starts[i] + delay_counts[i];
        if ((index >= delay_starts[i]) && (index < end)) {
            place_idx = i;
            break;
        }
    }

    //loop through all delay extension placements to send the appropriate pairs
    for (uint32_t place_i = 0; place_i < num_placements; place_i++) {

        log_debug("place 0x%04x", placements[place_idx]);

        prev_pre = 333;
        prev_dly = 333;
        uint32_t prev_plc_idx = place_idx - 1;
        if (place_idx == 0) {
            prev_plc_idx = num_placements - 1;
        }

        if (starts[prev_plc_idx] >= n_delays) {
            break;
        }
        index_seen = starts[place_idx];

        // seen[place_idx] = 1;
        while(index_seen < n_delays) {
            index = pre_slice_start + _preid_delay_i(delays[index_seen]);
            delay = _preid_delay_d(delays[index_seen]);

            if (prev_pre == index && prev_dly == delay) {
                index_seen++;
                continue;
            }

            delay_end = delay_starts[place_idx] + delay_counts[place_idx];

            if ((index >= delay_starts[place_idx]) && (index < delay_end)) {

                log_debug("index %u, delay %u, d-start %u, d-end %u",
                    index, delay, delay_starts[place_idx], delay_end);

                pairs_per_core[count] = delays[index_seen];
                count++;
            } else {
                for(uint32_t i = index_seen; i < num_placements; i++){
                uint32_t end = delay_starts[i] + delay_counts[i];
                if ((index >= delay_starts[i]) && (index < end) && !seen[i]) {
                  seen[i] = 1;
                  starts[i] = index_seen;
                  break;
                }
                }
            }

            if(count==MAX_N_DELAYS_PER_PACKET){
              send_n_delays(placements[place_idx], (uint16_t *)(&pairs_per_core), count,
                            rand_num, delay_starts[place_idx]);
              count = 0;
              spin1_delay_us(SLEEP_TIME);
              seen[place_idx] = 1;
            }
            prev_pre = index;
            prev_dly = delay;
            index_seen++;
            starts[place_idx] = index_seen;
        }

        if(count > 0){
          send_n_delays(placements[place_idx], (uint16_t *)(&pairs_per_core), count,
                        rand_num, delay_starts[place_idx]);
        }
        count = 0;

        if(seen[place_idx]){
        log_info("\t --- 0x%04x finished",
                  placements[place_idx]);

        send_n_delays(placements[place_idx], NULL, 0, rand_num, 0);
        }
        place_idx++;
        if(place_idx == num_placements){
        place_idx = 0;
        }
    }

//    for(uint32_t i = index_seen; i < num_placements; i++){
//      log_info("Seen placements %u", seen[i]);
//    }

    return true;
}

uint32_t max_matrix_size(
        uint32_t max_n_static, uint32_t max_n_plastic,
        uint32_t plastic_header) {
    // both plastic-plastic and plastic-fixed are 16-bit data

    uint32_t plastic_word_size = (max_n_plastic / 2) + (max_n_plastic % 2);
    log_debug("header: %u, static: %u, plastic: %u ; %u, def: 3",
        plastic_header, max_n_static, max_n_plastic, plastic_word_size);

    return 1 + plastic_header + max_n_plastic + 1 + 1 + max_n_static +
        plastic_word_size;

    // n_plastic was already multiplied before
    // return 1 + plastic_word_size + 1 + 1 + n_static + n_plastic;
}

bool read_connection_builder_region(
        address_t *in_region, address_t synaptic_matrix_region,
        uint32_t post_slice_start, uint32_t post_slice_count,
        int32_t *weight_scales, uint32_t num_synapse_bits,
        uint32_t num_static, uint32_t num_plastic){
    log_info("Reading Connection Builder Region");

    uint32_t *region = *in_region;

    // Read RNG seed for this matrix
    rng_t rng = rng_init(region);

    const uint32_t connector_type_hash = *region++;
    const uint32_t pre_key             = *region++;
    const uint32_t pre_mask            = *region++;
    const uint32_t address_delta       = *region++;
    const uint32_t row_len             = *region++;
    const uint32_t num_pre_neurons     = *region++;
    const uint32_t max_post_neurons    = *region++;
    const uint32_t words_per_weight    = *region++;
    const uint32_t pre_slice_start     = *region++;
    const uint32_t pre_slice_count     = *region++;
    const uint32_t is_direct_row       = *region++;
    const uint32_t is_delayed          = *region++;
    const uint32_t num_delayed_places  = *region++;

    const uint32_t *delay_places_xyp   = region;
    region += num_delayed_places;

    const uint32_t *delay_starts       = region;
    region += num_delayed_places;

    const uint32_t *delay_counts       = region;
    region += num_delayed_places;

    const uint32_t matrix_type_hash    = *region++;
    const uint32_t synapse_type        = *region++;

    const uint32_t weight_type_hash    = *region++;
    const uint32_t delay_type_hash     = *region++;

    log_info(
        "\t connector type hash:%u, delay type hash:%u, weight type hash:%u",
        connector_type_hash, delay_type_hash, weight_type_hash);

    log_info(
        "\t key: %08x, mask: %08x, address delta: %u",
        pre_key, pre_mask, address_delta);

    log_info(
        "\t pre slice (%u, %u of %u), post slice (%u, %u)",
            pre_slice_start, pre_slice_start + pre_slice_count, num_pre_neurons,
            post_slice_start, post_slice_start + post_slice_count);

    log_info("\t number of delay extension cores: %u", num_delayed_places);
    for (uint32_t i = 0; i < num_delayed_places; i++) {
        log_info(
            "\t delay: place (%u, %u, %u), slice (%u:%u)",
            _place_x(delay_places_xyp[i]), _place_y(delay_places_xyp[i]),
            _place_p(delay_places_xyp[i]), delay_starts[i], delay_counts[i]);
    }


    log_info("\t direct? %u, delayed? %u", is_direct_row, is_delayed);

    log_info(
        "\t synapse (plastic/static) hash %u, synapse type  %u, ",
        matrix_type_hash, synapse_type);

    // Generate matrix, connector, delays and weights
    matrix_generator = matrix_generator_init(matrix_type_hash, &region);
    connection_generator = connection_generator_init(
        connector_type_hash, &region);
    weight_generator = param_generator_init(weight_type_hash, &region);
    delay_generator = param_generator_init(delay_type_hash, &region);

    *in_region = region;

    // If any components couldn't be created return false
    if (matrix_generator == NULL || connection_generator == NULL
            || delay_generator == NULL || weight_generator == NULL) {
        return false;
    }

    log_debug("max num static: %u, max num plastic: %u, row_len: %u",
        num_static, num_plastic, row_len);
    if (matrix_generator_is_static(matrix_generator)) {
        // num_static = max_post_neurons;
        num_static = row_len;
    } else if (row_len > 0) {
        // diff means 2*(max plastic words)? and we can have 2 plastic
        // control/weights per word, so to get max num plastic =
        // 2 * (row_len - stateWords) / 2 which means we shouldn't do a thing!
        // num_plastic = (row_len - matrixGenerator->m_PreStateWords);
        // num_plastic = (num_plastic/2 + num_plastic%2);
        num_plastic = max_post_neurons;
    } else {
        num_plastic = 0;
    }

    if (num_plastic == 0 && num_static == 0) {
        log_debug("no static nor plastic - synaptic matrix size = %u",
            synaptic_matrix_region[0] >> 2);
        synaptic_matrix_region[(synaptic_matrix_region[0] >> 2) + 1] = 0;
        return true;
    }

    uint32_t per_pre_size = max_matrix_size(
        num_static, num_plastic,
        matrix_generator_n_pre_state_words(matrix_generator));
    log_debug(
        "max num static: %u, max num plastic: %u, max matrix size: %u",
         num_static, num_plastic, per_pre_size);

    // Generate matrix
    uint32_t pre_slice_end = pre_slice_start + pre_slice_count;
    for (uint32_t pre_start_new = pre_slice_start;
            pre_start_new < pre_slice_end;
            pre_start_new += MAX_PRE_DELAY_ENTRIES) {

        uint32_t pre_count_new = MAX_PRE_DELAY_ENTRIES;

        log_debug("start %u, end %u, count %u",
            pre_start_new, pre_start_new + pre_count_new, pre_count_new);

        if (pre_start_new + pre_count_new > pre_slice_end) {
            pre_count_new = pre_slice_end - pre_start_new;
        }

#ifdef DEBUG_MESSAGES
        if (pre_start_new % 5000 == 0) {
            log_info(
                "%u -> %u\n", pre_start_new, pre_start_new + pre_count_new);
        }
#endif

        uint16_t pair_count = 0;
        spin1_delay_us(spin1_get_core_id());
        if (!matrix_generator_generate(
                matrix_generator,
                synaptic_matrix_region, address_delta, num_static, num_plastic,
                per_pre_size, synapse_type, post_slice_start, post_slice_count,
                pre_slice_start, pre_slice_count,
                pre_start_new, pre_count_new, words_per_weight,
                weight_scales, num_synapse_bits, connection_generator,
                delay_generator, weight_generator, rng, pre_delay_pairs,
                pair_count)){
            log_error("\tMatrix generation failed");
            return false;
        }

#ifdef DEBUG_MESSAGES
        for (uint32_t i = 0; i < pair_count; i++) {
            log_info("pre id = %u, delay = %u",
                _preid_delay_i(pre_delay_pairs[i]),
                _preid_delay_d(pre_delay_pairs[i]));
        }
        log_info("delayed pairs %u", pair_count);
#endif
        if (pair_count > 0) {
            if (!send_delays(num_delayed_places, delay_places_xyp,
                    delay_starts, delay_counts, pair_count, pre_delay_pairs,
                    pre_slice_start, rng)) {
                return false;
            }
        }
    }

    return true;
}

//-----------------------------------------------------------------------------

void clear_memory(uint32_t *syn_mtx_addr){

  for(uint32_t w = 0; w < (syn_mtx_addr[0] >> 2); w++){
    syn_mtx_addr[1+w] = 0;
  }
}


bool read_sdram_data(address_t params_address, address_t syn_mtx_addr){
    uint32_t mem_tag = ID_DELAY_SDRAM_TAG + spin1_get_core_id();

    log_info("Allocating up memory for tag %u", mem_tag);
    #if SARK_HEAP == 1
        log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, ALLOC_LOCK));
    #else
        log_info("%u bytes of free SDRAM",
            sark_heap_max(sv->sdram_heap, ALLOC_LOCK));
    #endif

    log_info("index/delay buffer size = %u bytes",
        (MAX_PRE_DELAY_ENTRIES*256)*sizeof(uint16_t));

    #if SARK_HEAP == 1
        pre_delay_pairs = (uint16_t *) sark_xalloc(
            sark.heap, (MAX_PRE_DELAY_ENTRIES * 256) * sizeof(uint16_t),
            mem_tag, ALLOC_LOCK);
    #else
        pre_delay_pairs = (uint16_t *) sark_xalloc(
            sv->sdram_heap, (MAX_PRE_DELAY_ENTRIES * 256) * sizeof(uint16_t),
            mem_tag, ALLOC_LOCK);
    #endif


    if (pre_delay_pairs == NULL){
        log_error("Unable to allocate memory for pre-delay pairs");
        return false;
    }

#ifdef DEBUG_MESSAGES
    log_info("Synaptic Matrix Address: 0x%08x", syn_mtx_addr);
    for (uint32_t i = 0; i < (syn_mtx_addr[0] >> 2) + 1; i++) {
        log_info("syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
    }
#endif
    uint32_t *clear_memory_ptr = (uint32_t *) sark_tag_ptr(
        SDRAM_TAG + spin1_get_core_id(), sark_app_id());
    log_debug("clear_memory_ptr = 0x%08x", clear_memory_ptr);
    log_debug("clear_memory_flag = 0x%08x", *clear_memory_ptr);

    uint32_t num_in_edges = *params_address++;
    log_debug("Num in edges = %u", num_in_edges);

    // ceil(num_edges/32.0);
    uint32_t num_flag_words = (num_in_edges + 31) >> 5;
    log_debug("Num flag words = %u", num_flag_words);

    uint32_t *build_flags = params_address;
    params_address += num_flag_words;


#ifdef DEBUG_MESSAGES
    for (uint32_t i = 0; i < num_flag_words; i++) {
        log_info("build_flags[%u] = 0x%08x", i, build_flags[i]);
    }
#endif

    if (*clear_memory_ptr == CLEAR_MEMORY_FLAG){
        log_info("CLEARING MEMORY!!! --------------------------------");
        clear_memory(syn_mtx_addr);
    }

#ifdef DEBUG_MESSAGES
    for (uint32_t i = 0; i < (syn_mtx_addr[0] >> 2) + 1; i++) {
        log_info("syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
    }
#endif

    uint32_t post_slice_start = *params_address++;
    uint32_t post_slice_count = *params_address++;
    log_debug("post slice: start %u, count %u",
        post_slice_start, post_slice_count);

    uint32_t num_synapse_types = *params_address++;
    uint32_t num_synapse_bits  = *params_address++;

    int32_t *weight_scales = (int32_t *) params_address;
    params_address += num_synapse_types;
    log_debug("num_synapse_types = %u", num_synapse_types);

    int32_t min_weight_scale = 100000;
    // weight_scales[0] -= 1;
    for (uint32_t i = 0; i < num_synapse_types; i++) {
        log_info("Weight scale %u = %u", i, weight_scales[i]);
        if (weight_scales[i] < min_weight_scale) {
            min_weight_scale = weight_scales[i];
        }
    }

    // how many bytes to read for all connections
    uint32_t params_size = *params_address++;
    log_info("\tParameter block size = %u", params_size);

    uint32_t num_static = 0; // *params_address++;
    uint32_t num_plastic = 0; // *params_address++;

#ifdef DEBUG_MESSAGES
    log_info("synaptic matrix address = 0x%08x", syn_mtx_addr);
    for (uint32_t i = 0; i < (syn_mtx_addr[0] >> 2) + 10; i++) {
        log_info("syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
    }
#endif

    for (uint32_t w = 0; w < num_flag_words; w++) {
        for (uint32_t edge = 0; edge < 32; edge++) {
            uint32_t edge_mask = 1 << edge;
            if ((build_flags[w] & edge_mask) != 0) {
                log_info("0x%08x <=> 0x%08x", build_flags[w], edge_mask);

                log_info("\n\n= = = = = =\n\n");
                if (!read_connection_builder_region(
                        &params_address, syn_mtx_addr, post_slice_start,
                        post_slice_count, weight_scales, num_synapse_bits,
                        num_static, num_plastic)) {
                    log_info("Failed to generate synaptic matrix for edge %u",
                        edge);
                    return false;
                }

                #ifdef DEBUG_MESSAGES
                log_info("AFTER: params and synapse address 0x%08x\t0x%08x",
                    params_address, syn_mtx_addr);
                log_info("synaptic matrix size = %u", syn_mtx_addr[0] >> 2);
                for (uint32_t i = 0; i < (syn_mtx_addr[0] >> 2)+2; i++) {
                    log_info("syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
                }
                #endif
            }
        }
    }


    log_info("\n\n= = = = = =\n\n");
#ifdef DEBUG_MESSAGES
    if ((syn_mtx_addr[0] >> 2) < 81) {
        log_info("synaptic matrix address = 0x%08x", syn_mtx_addr);
        for (uint32_t i = 0; i < (syn_mtx_addr[0] >> 2) + 1; i++) {
            log_info("syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
        }
    }

    log_info("indirect synaptic matrix size %d", (syn_mtx_addr[0] >> 2));

    log_info("syn_mtx_addr[%u] = %d", (syn_mtx_addr[0] >> 2) + 1,
        syn_mtx_addr[(syn_mtx_addr[0] >> 2)+1]);

    log_info("syn_mtx_addr[%u] = %d", (syn_mtx_addr[0] >> 2) + 2,
        syn_mtx_addr[(syn_mtx_addr[0] >> 2)+2]);

    log_info("Freeing memory for tag %u", mem_tag);
#endif

    #if SARK_HEAP == 1
        sark_xfree(sark.heap, pre_delay_pairs, ALLOC_LOCK);
    #else
        sark_xfree(sv->sdram_heap, pre_delay_pairs, ALLOC_LOCK);
    #endif
    pre_delay_pairs = NULL;

    log_debug("\tFreed");

    sark_xfree(sv->sdram_heap, clear_memory_ptr, ALLOC_LOCK);

    //  TODO: params memory is no longer needed, is there a way to free it?
    //  sark_xfree(sv->sdram_heap, params_address, ALLOC_LOCK);

    return true;
    }

void app_start(uint a0, uint a1) {
    _unused(a0);
    _unused(a1);

    // Register matrix generators with factories
    // **NOTE** plastic matrix generator is capable of generating
    // both standard and extended plastic matrices
    // log_info("Matrix generators");
    // REGISTER_FACTORY_CLASS("StaticSynapticMatrix", MatrixGenerator, Static);
    // REGISTER_FACTORY_CLASS("PlasticSynapticMatrix", MatrixGenerator, Plastic);
    // REGISTER_FACTORY_CLASS("ExtendedPlasticSynapticMatrix", MatrixGenerator, Plastic);
    register_matrix_generators();

    // Register connector generators with factories
    // log_info("Connector generators");
    // REGISTER_FACTORY_CLASS("AllToAllConnector", ConnectorGenerator, AllToAll);
    // REGISTER_FACTORY_CLASS("OneToOneConnector", ConnectorGenerator, OneToOne);
    // REGISTER_FACTORY_CLASS("FixedProbabilityConnector", ConnectorGenerator, FixedProbability);
    // REGISTER_FACTORY_CLASS("KernelConnector", ConnectorGenerator, Kernel);
    // REGISTER_FACTORY_CLASS("MappingConnector", ConnectorGenerator, Mapping);
    // REGISTER_FACTORY_CLASS("FixedTotalNumberConnector", ConnectorGenerator, FixedTotalNumber);
    register_connection_generators();

    // Register parameter generators with factories
    // log_info("Parameter generators");
    // REGISTER_FACTORY_CLASS("constant", ParamGenerator, Constant);
    // REGISTER_FACTORY_CLASS("kernel",   ParamGenerator, ConvKernel);
    // REGISTER_FACTORY_CLASS("uniform",  ParamGenerator, Uniform);
    // REGISTER_FACTORY_CLASS("normal",   ParamGenerator, Normal);
    //  REGISTER_FACTORY_CLASS("normal_clipped", ParamGenerator, NormalClipped);
    //  REGISTER_FACTORY_CLASS("normal_clipped_to_boundary", ParamGenerator, NormalClippedToBoundary);
    // REGISTER_FACTORY_CLASS("exponential", ParamGenerator, Exponential);
    register_param_generators();

    // Allocate buffers for placement new from factories
    // **NOTE** we need to be able to simultaneously allocate a delay and
    // a weight generator so we need two buffers for parameter allocation
    // g_MatrixGeneratorBuffer = g_MatrixGeneratorFactory.Allocate();
    // g_ConnectorGeneratorBuffer = g_ConnectorGeneratorFactory.Allocate();
    // g_DelayParamGeneratorBuffer = g_ParamGeneratorFactory.Allocate();
    // g_WeightParamGeneratorBuffer = g_ParamGeneratorFactory.Allocate();

    // Get this core's base address using alloc tag
    // uint32_t *params_address = Config::GetBaseAddressAllocTag();
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    log_info("Starting To Build Connectors");
    // If reading SDRAM data fails

    address_t core_address = data_specification_get_data_address();
    address_t sdram_address = data_specification_get_region(
        CONNECTOR_BUILDER_REGION, core_address);
    address_t syn_mtx_addr = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, core_address);

    log_info("\tReading SDRAM at 0x%08x", sdram_address);

    if (!read_sdram_data(sdram_address, syn_mtx_addr)) {
        log_info("!!!   Error reading SDRAM data   !!!");
        rt_error(RTE_ABORT);
    }

    log_info("Finished On Machine Connectors!");
    spin1_exit(0);
}

void c_main(void){
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    // kick-start the process
    spin1_schedule_callback(app_start, 0, 0, 2);
    spin1_callback_on(SDP_PACKET_RX, handle_sdp_message, 0);

    // go
    spin1_start(SYNC_NOWAIT);
}
