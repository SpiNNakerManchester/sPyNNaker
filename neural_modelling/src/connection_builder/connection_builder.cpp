#include "connection_builder.h"

// extern "C"{
//   #include <data_specification.h>
// }

// Common includes
#include "./common/key_lookup_binary_search.h"

// Connection builder includes
#include "connector_generator.h"
#include "generator_factory.h"
#include "matrix_generator.h"
#include "param_generator.h"


//#define DEBUG_MESSAGES
#define SARK_HEAP 1

// Namespaces
using namespace Common;
using namespace Common::Random;
using namespace ConnectionBuilder;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{
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

// Config g_Config;
// KeyLookupBinarySearch<10> g_KeyLookup;

// uint32_t g_AppWords[AppWordMax];

uint32_t *g_SynapticMatrixBaseAddress = NULL;

// Factories to create matrix, connector and parameter generators by ID
GeneratorFactory<MatrixGenerator::Base, 2> g_MatrixGeneratorFactory;
GeneratorFactory<ConnectorGenerator::Base, 5> g_ConnectorGeneratorFactory;
GeneratorFactory<ParamGenerator::Base, 10> g_ParamGeneratorFactory;

// Memory buffers to placement new generators into
void *g_MatrixGeneratorBuffer = NULL;
void *g_ConnectorGeneratorBuffer = NULL;
void *g_DelayParamGeneratorBuffer = NULL;
void *g_WeightParamGeneratorBuffer = NULL;

uint32_t *sdram_address = NULL;


static void handle_sdp_message(uint mailbox, uint sdp_port) {
    LOG_PRINT(LOG_LEVEL_INFO, "\t\tACK rec");
    delay_response_received = true;
}

static void wait_for_delay_response(uint32_t rand_num) {
//  spin1_delay_us(SLEEP_TIME);
  int retry_count = 0;
  // Wait until the response to the last message has been received
  LOG_PRINT(LOG_LEVEL_INFO, "\t - Waiting for ACK");
  while (!delay_response_received) {
    if (retry_count >= MAX_RETRIES){
//      rt_error(RTE_ABORT);
      delay_response_received = true;
  //   spin1_exit(0); //error!!!
      break;
    }

  //   Wait for a time for a response
  //   LOG_PRINT(LOG_LEVEL_INFO, "Waiting for response from last delay message");
    uint32_t shift = (spin1_get_core_id()*spin1_get_chip_id() + retry_count)%28;
    spin1_delay_us(SLEEP_TIME + 2*((rand_num >> shift) & 3) +
                  ((rand_num >> (shift+2)) & 3));

     // Re-send the message
    if (!delay_response_received) {
      spin1_send_sdp_msg(&delay_message, 1);
      retry_count++;
    }
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\t\t - Waited %u times", retry_count);
}

static void send_n_delays(uint32_t placement, uint16_t *delays, uint32_t n_delays,
                          const uint32_t rand_num, const uint32_t pre_slice_start){

  uint16_t delay_chip = (uint16_t)_place_xy_16(placement);
  uint8_t delay_core  = (uint8_t)_place_p(placement);
//#ifdef DEBUG_MESSAGES
  LOG_PRINT(LOG_LEVEL_INFO,
            "send_n_delays to 0x%04x.%02u, N = %u",
            delay_chip, delay_core, n_delays);
//  for(uint32_t i = 0; i < n_delays; i++){
//    LOG_PRINT(LOG_LEVEL_INFO,
//              "\tpre = %u, delay = %u", _preid_delay_i(delays[i]),
//              _preid_delay_d(delays[i]));
//  }
//#endif
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


  spin1_delay_us(1+(rand_num >>  spin1_get_core_id()) & 3);
  delay_response_received = false;
  spin1_send_sdp_msg(&delay_message, 1);
  wait_for_delay_response(rand_num);

}

// Sends delays to the delay core
static bool send_delays(const uint32_t num_placements, const uint32_t *placements,
                        const uint32_t *delay_starts, const uint32_t *delay_counts,
                        uint16_t n_delays, uint16_t *delays, uint32_t pre_slice_start,
                        const uint32_t rand_num) {

    if (n_delays == 0) {
        return true;
    }

    LOG_PRINT(LOG_LEVEL_INFO, "In send delays");


    uint16_t pairs_per_core[MAX_N_DELAYS_PER_PACKET];

    uint32_t starts[num_placements];
    for(uint32_t i = 0; i < num_placements; i++){
      starts[i] = 0;
    }

    uint16_t seen[num_placements];
    for(uint32_t i = 0; i < num_placements; i++){
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
    //Find placement for first id/delay pair
    index = pre_slice_start + _preid_delay_i(delays[0]);
    for(uint32_t i = 0; i < num_placements; i++){
        uint32_t end = delay_starts[i] + delay_counts[i];
      if( (index >= delay_starts[i]) && (index < end) ){
        place_idx = i;
        break;
      }
    }
    //loop through all delay extension placements to send the appropriate
    //pairs
    for(uint32_t place_i = 0; place_i < num_placements; place_i++){

#ifdef DEBUG_MESSAGES
      LOG_PRINT(LOG_LEVEL_INFO, "place 0x%04x", placements[place_idx]);
#endif
      prev_pre = 333;
      prev_dly = 333;
      uint32_t prev_plc_idx = place_idx - 1;
      if(place_idx == 0){
        prev_plc_idx = num_placements - 1;
      }

      if(starts[prev_plc_idx] >= n_delays){
        break;
      }
      index_seen = starts[place_idx];

//      seen[place_idx] = 1;
      while(index_seen < n_delays){
        index = pre_slice_start + _preid_delay_i(delays[index_seen]);
        delay = _preid_delay_d(delays[index_seen]);

        if(prev_pre == index && prev_dly == delay){
          index_seen++;
          continue;
        }

        delay_end = delay_starts[place_idx] + delay_counts[place_idx];

        if( (index >= delay_starts[place_idx]) && (index < delay_end) ){

//#ifdef DEBUG_MESSAGES
//          LOG_PRINT(LOG_LEVEL_INFO, "idx %u, dly %u, d-start %u, d-end %u",
//                    index, delay, delay_starts[place_idx], delay_end);
//#endif

          pairs_per_core[count] = delays[index_seen];
          count++;
        }
        else{
          for(uint32_t i = index_seen; i < num_placements; i++){
            uint32_t end = delay_starts[i] + delay_counts[i];
            if( (index >= delay_starts[i]) && (index < end) && !seen[i]){
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
        LOG_PRINT(LOG_LEVEL_INFO, "\t --- 0x%04x finished",
                  placements[place_idx]);

        send_n_delays(placements[place_idx], NULL, 0, rand_num, 0);
      }
      place_idx++;
      if(place_idx == num_placements){
        place_idx = 0;
      }
    }

//    for(uint32_t i = index_seen; i < num_placements; i++){
//      LOG_PRINT(LOG_LEVEL_INFO, "Seen placementes %u", seen[i]);
//    }

    return true;
}



uint32_t max_matrix_size(uint32_t max_n_static, uint32_t max_n_plastic,
                         uint32_t plastic_header){
  // both plastic-plastic and plastic-fixed are 16-bit data

  uint32_t plastic_word_size = (max_n_plastic/2 + max_n_plastic%2);
//  LOG_PRINT(LOG_LEVEL_INFO, "header: %u, static: %u, plastic: %u ; %u, def: 3",
//            plastic_header, max_n_static, max_n_plastic, plastic_word_size);

  return 1 + plastic_header + max_n_plastic +
         1 + 1 + max_n_static + plastic_word_size;
  //n_plastic was already multiplied before
//  return 1 + plastic_word_size + 1 + 1 + n_static + n_plastic;

}
//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
bool ReadSynapticMatrixRegion(uint32_t *region, uint32_t)
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadSynapticMatrixRegion");

  // Cache pointer to region as base address for synaptic matrices
  g_SynapticMatrixBaseAddress = region;

  LOG_PRINT(LOG_LEVEL_INFO, "\tSynaptic matrix base address:%08x",
            g_SynapticMatrixBaseAddress);

  return true;
}
//-----------------------------------------------------------------------------
bool ReadConnectionBuilderRegion(uint32_t **in_region,
                                 uint32_t *synaptic_matrix_region,
                                 uint32_t post_slice_start,
                                 uint32_t post_slice_count,
                                 int32_t *weight_scales,
                                 uint32_t num_synapse_bits,
                                 uint32_t num_static,
                                 uint32_t num_plastic){
  LOG_PRINT(LOG_LEVEL_INFO, "Reading Connection Builder Region");

  uint32_t *region = *in_region;

  // Read RNG seed for this matrix
  uint32_t seed[MarsKiss64::StateSize];
//  LOG_PRINT(LOG_LEVEL_INFO, "\tSeed:"); // where LOG_LEVEL_TRACE
  for(unsigned int s = 0; s < MarsKiss64::StateSize; s++)
  {
    seed[s] = *region++;
//    LOG_PRINT(LOG_LEVEL_INFO, "\t\t%u", seed[s]);
  }
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


  // Create RNG with this seed for this matrix
  MarsKiss64 rng(seed);
//#if LOG_LEVEL <= LOG_LEVEL_TRACE
#ifdef DEBUG_MESSAGES
  LOG_PRINT(LOG_LEVEL_INFO, "\tconnector type hash:%u, delay type hash:%u, weight type hash:%u", connector_type_hash, delay_type_hash, weight_type_hash);

  LOG_PRINT(LOG_LEVEL_INFO, "\tkey: %08x, mask: %08x, address delta: %u",
            pre_key, pre_mask, address_delta);

  LOG_PRINT(LOG_LEVEL_INFO, "\tpre slice (%u, %u of %u), post slice (%u, %u)",
            pre_slice_start, pre_slice_start + pre_slice_count, num_pre_neurons,
            post_slice_start, post_slice_start + post_slice_count);

  LOG_PRINT(LOG_LEVEL_INFO, "\tnumber of delay extension cores: %u",
            num_delayed_places);
  for(uint32_t i = 0; i < num_delayed_places; i++){
    LOG_PRINT(LOG_LEVEL_INFO, "\tdelay: place (%u, %u, %u), slice (%u:%u)",
             _place_x(delay_places_xyp[i]), _place_y(delay_places_xyp[i]),
             _place_p(delay_places_xyp[i]), delay_starts[i], delay_counts[i]);
  }


  LOG_PRINT(LOG_LEVEL_INFO, "\tdirect? %u, delayed? %u, ",
            is_direct_row, is_delayed);

  LOG_PRINT(LOG_LEVEL_INFO,
            "\tsynapse (plastic/static) hash %u, synapse type (exc, inh, etc.) %u, ",
            matrix_type_hash, synapse_type);
#endif

  // Generate matrix, connector, delays and weights
  const auto matrixGenerator = g_MatrixGeneratorFactory.Create(
                                   matrix_type_hash, region,
                                   g_MatrixGeneratorBuffer);

  const auto connectorGenerator = g_ConnectorGeneratorFactory.Create(connector_type_hash,
                                                     region, g_ConnectorGeneratorBuffer);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tWeight");
  const auto weightGenerator = g_ParamGeneratorFactory.Create(weight_type_hash,
                                         region, g_WeightParamGeneratorBuffer);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tDelay");
  const auto delayGenerator = g_ParamGeneratorFactory.Create(delay_type_hash,
                                         region, g_DelayParamGeneratorBuffer);

  *in_region = region;

  // If any components couldn't be created return false
  if(matrixGenerator == NULL || connectorGenerator == NULL
    || delayGenerator == NULL || weightGenerator == NULL)
  {
    return NULL;
  }
#ifdef DEBUG_MESSAGES
  LOG_PRINT(LOG_LEVEL_INFO, "max num static: %u, max num plastic: %u, row_len: %u",
            num_static, num_plastic, row_len);
#endif

  if(matrixGenerator->is_static){
//    num_static = max_post_neurons;
    num_static = row_len;
  }
  else{
    if(row_len > 0){
      //diff means 2*(max plastic words)? and we can have 2 plastic control/weights
      //per word, so to get max num plastic = 2(row_len - stateWords)/2
      //which means we shouldn't do a thing!
//      num_plastic = (row_len - matrixGenerator->m_PreStateWords);
//      num_plastic = (num_plastic/2 + num_plastic%2);
      num_plastic = max_post_neurons;
    }else{
      num_plastic = 0;
    }
  }

  if(num_plastic == 0 && num_static == 0){

//        LOG_PRINT(LOG_LEVEL_INFO, "no static nor plastic - synaptic matrix size = %u",
//                  synaptic_matrix_region[0] >> 2);
    synaptic_matrix_region[(synaptic_matrix_region[0] >> 2) + 1] = 0;

    return true;
  }


  uint32_t per_pre_size = max_matrix_size(num_static, num_plastic,
                                          matrixGenerator->m_PreStateWords);
#ifdef DEBUG_MESSAGES
  LOG_PRINT(LOG_LEVEL_INFO,
            "max num static: %u, max num plastic: %u, max matrix size: %u",
             num_static, num_plastic, per_pre_size);
#endif

  // Generate matrix


  uint32_t pre_slice_end = pre_slice_start + pre_slice_count;
  for(uint32_t pre_start_new = pre_slice_start; pre_start_new < pre_slice_end;
      pre_start_new += MAX_PRE_DELAY_ENTRIES){

    uint32_t pre_count_new = MAX_PRE_DELAY_ENTRIES;

//    LOG_PRINT(LOG_LEVEL_INFO, "start %u, end %u, count %u",
//              pre_start_new, pre_start_new + pre_count_new, pre_count_new);

    if(pre_start_new + pre_count_new > pre_slice_end){
      pre_count_new = pre_slice_end - pre_start_new;
    }

//    if(pre_start_new%5000 == 0){
//        io_printf(IO_BUF, "%u -> %u\n",
//                  pre_start_new, pre_start_new + pre_count_new);
//    }

    uint16_t pair_count = 0;
    spin1_delay_us(spin1_get_core_id());
    if(!matrixGenerator->Generate(synaptic_matrix_region, address_delta,
                                  num_static, num_plastic,
                                  per_pre_size, synapse_type,
                                  post_slice_start, post_slice_count,
                                  pre_key, pre_mask,
                                  pre_slice_start, pre_slice_count,
                                  pre_start_new, pre_count_new,
                                  num_pre_neurons, words_per_weight,
                                  weight_scales, num_synapse_bits,
                                  connectorGenerator, delayGenerator, weightGenerator,
                                  rng, pre_delay_pairs, pair_count)){
      LOG_PRINT(LOG_LEVEL_ERROR, "\tMatrix generation failed");
      return false;
    }

    //  for(uint32_t i = 0; i < pair_count; i++){
    //    LOG_PRINT(LOG_LEVEL_INFO, "pre id = %u, delay = %u",
    //    _preid_delay_i(pre_delay_pairs[i]), _preid_delay_d(pre_delay_pairs[i]));
    //  }
//    LOG_PRINT(LOG_LEVEL_INFO, "delayed pairs %u", pair_count);
    if(pair_count > 0){
      if( !send_delays(num_delayed_places, delay_places_xyp,
                       delay_starts, delay_counts,
                       pair_count, pre_delay_pairs,
                       pre_slice_start,
                       seed[spin1_get_core_id()%4])){
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


bool ReadSDRAMData(uint32_t *params_address, uint32_t *syn_mtx_addr){

  uint32_t mem_tag = ID_DELAY_SDRAM_TAG + spin1_get_core_id();

//#ifdef DEBUG_MESSAGES
  LOG_PRINT(LOG_LEVEL_INFO, "Allocating up memory for tag %u", mem_tag);
#if SARK_HEAP == 1
  LOG_PRINT(LOG_LEVEL_INFO, "%u bytes of free DTCM",
            sark_heap_max(sark.heap, ALLOC_LOCK));
#else
  LOG_PRINT(LOG_LEVEL_INFO, "%u bytes of free SDRAM",
            sark_heap_max(sv->sdram_heap, ALLOC_LOCK));
#endif

//#endif

  LOG_PRINT(LOG_LEVEL_INFO, "idx/delay buffer size = %u bytes",
            (MAX_PRE_DELAY_ENTRIES*256)*sizeof(uint16_t) );

#if SARK_HEAP == 1
  pre_delay_pairs = (uint16_t *)sark_xalloc(sark.heap,
#else
  pre_delay_pairs = (uint16_t *)sark_xalloc(sv->sdram_heap,
#endif
                               (MAX_PRE_DELAY_ENTRIES*256)*sizeof(uint16_t),
                                mem_tag, ALLOC_LOCK);

  if(pre_delay_pairs == NULL){
    LOG_PRINT(LOG_LEVEL_INFO, "%u bytes of free SDRAM",
              sark_heap_max(sv->sdram_heap, ALLOC_LOCK));
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate memory for pre-delay pairs");
    return false;
  }

//  LOG_PRINT(LOG_LEVEL_INFO, "Synaptic Matrix Address: 0x%08x", syn_mtx_addr);
//  for(uint32_t i = 0; i < (syn_mtx_addr[0] >> 2) + 1; i++){
//      LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
//  }
  uint32_t *clear_memory_ptr = (uint32_t *) sark_tag_ptr(SDRAM_TAG + spin1_get_core_id(),
                                                         sark_app_id());
//  LOG_PRINT(LOG_LEVEL_INFO, "clear_memory_ptr = 0x%08x", clear_memory_ptr);

//  LOG_PRINT(LOG_LEVEL_INFO, "clear_memory_flag = 0x%08x", *clear_memory_ptr);

  uint32_t num_in_edges = *params_address++;
//  LOG_PRINT(LOG_LEVEL_INFO, "Num in edges = %u", num_in_edges);

  uint32_t num_flag_words = (num_in_edges + 31) >> 5; //ceil(num_edges/32.0);
//  LOG_PRINT(LOG_LEVEL_INFO, "Num flag words = %u", num_flag_words);

  uint32_t *build_flags = params_address;
  params_address += num_flag_words;


//  for(uint32_t i = 0; i < num_flag_words; i++){
//      LOG_PRINT(LOG_LEVEL_INFO, "build_flags[%u] = 0x%08x", i, build_flags[i]);
//  }

  if(*clear_memory_ptr == CLEAR_MEMORY_FLAG){
//    LOG_PRINT(LOG_LEVEL_INFO, "CLEARING MEMORY!!! --------------------------------");
    clear_memory(syn_mtx_addr);
  }
//  for(uint32_t i = 0; i < (syn_mtx_addr[0] >> 2) + 1; i++){
//      LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
//  }

  uint32_t post_slice_start = *params_address++;


  uint32_t post_slice_count = *params_address++;
//  LOG_PRINT(LOG_LEVEL_INFO, "post slice: start %u, count %u",
//            post_slice_start, post_slice_count);

  uint32_t num_synapse_types = *params_address++;
  uint32_t num_synapse_bits  = *params_address++;

  int32_t *weight_scales = (int32_t *)params_address;
  params_address += num_synapse_types;
//  LOG_PRINT(LOG_LEVEL_INFO, "num_synapse_types = %u", num_synapse_types);

  uint32_t min_weight_scale = 100000;
//  weight_scales[0] -= 1;
  for(uint32_t i = 0; i < num_synapse_types; i++){
//    LOG_PRINT(LOG_LEVEL_INFO, "Weight scale %u = %u", i, weight_scales[i]);
    if ( weight_scales[i] < min_weight_scale ){
      min_weight_scale = weight_scales[i];
    }
  }


  uint32_t params_size = *params_address++; //how many bytes to read for all conns
//  LOG_PRINT(LOG_LEVEL_INFO, "\tParameter block size = %u", params_size);

  uint32_t num_static = 0;//*params_address++;
  uint32_t num_plastic = 0;//*params_address++;

// DEBUG:
//  LOG_PRINT(LOG_LEVEL_INFO, "synaptic matrix address = 0x%08x", syn_mtx_addr);
//  for(uint32_t i = 0; i < (syn_mtx_addr[0] >> 2)+10; i++){
//      LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
//  }

  uint32_t *conn_bldr_params = params_address;
  for(uint32_t w = 0; w < num_flag_words; w++){
    for(uint32_t edge = 0; edge < 32; edge++){
      uint32_t edge_mask = 1 << edge;
      if( (build_flags[w] & edge_mask) != 0){
//        LOG_PRINT(LOG_LEVEL_INFO, "0x%08x <=> 0x%08x", build_flags[w], edge_mask);

        LOG_PRINT(LOG_LEVEL_INFO,
        "\n\n= = = = = =\n\n");
        if( !ReadConnectionBuilderRegion(&params_address, syn_mtx_addr,
                                         post_slice_start, post_slice_count,
                                         weight_scales, num_synapse_bits,
                                         num_static, num_plastic) ){
          LOG_PRINT(LOG_LEVEL_INFO,
                    "!!!   Failed to generate synaptic matrix for edge %u   !!!",
                    edge);
          return false;
        }
//#ifdef DEBUG_MESSAGES
//        LOG_PRINT(LOG_LEVEL_INFO, "AFTER: params and syn addr 0x%08x\t0x%08x",
//                  params_address, syn_mtx_addr);
//        LOG_PRINT(LOG_LEVEL_INFO, "synaptic matrix size = %u",
//                  syn_mtx_addr[0] >> 2);
//        for(uint32_t i = 0; i < (syn_mtx_addr[0] >> 2)+2; i++){
//          LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
//        }
//#endif
      }
    }
  }


  LOG_PRINT(LOG_LEVEL_INFO, "\n\n= = = = = =\n\n");
#ifdef DEBUG_MESSAGES
  if((syn_mtx_addr[0] >> 2) < 81){
    LOG_PRINT(LOG_LEVEL_INFO, "synaptic matrix address = 0x%08x", syn_mtx_addr);
    for(uint32_t i = 0; i < (syn_mtx_addr[0] >> 2)+1; i++){
      LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %u", i, syn_mtx_addr[i]);
    }
  }

  LOG_PRINT(LOG_LEVEL_INFO, "indirect syn mtx size %d", (syn_mtx_addr[0] >> 2));

  LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %d", (syn_mtx_addr[0] >> 2)+1,
            syn_mtx_addr[(syn_mtx_addr[0] >> 2)+1]);

  LOG_PRINT(LOG_LEVEL_INFO, "syn_mtx_addr[%u] = %d", (syn_mtx_addr[0] >> 2)+2,
            syn_mtx_addr[(syn_mtx_addr[0] >> 2)+2]);

  LOG_PRINT(LOG_LEVEL_INFO, "Freeing memory for tag %u", mem_tag);
#endif

#if SARK_HEAP == 1
  sark_xfree (sark.heap, pre_delay_pairs, ALLOC_LOCK);
#else
  sark_xfree (sv->sdram_heap, pre_delay_pairs, ALLOC_LOCK);
#endif
  pre_delay_pairs = NULL;

#ifdef DEBUG_MESSAGES
    LOG_PRINT(LOG_LEVEL_INFO, "\tFreed");
#endif


  sark_xfree(sv->sdram_heap, clear_memory_ptr, ALLOC_LOCK);

//  TODO: params memory is no longer needed, is there a way to free it?
//  sark_xfree(sv->sdram_heap, params_address, ALLOC_LOCK);

  return true;

}



void app_start(uint a0, uint a1){
  _unused(a0);
  _unused(a1);
  sark_cpu_state(CPU_STATE_RUN);



  // Register matrix generators with factories
  // **NOTE** plastic matrix generator is capable of generating
  // both standard and extended plastic matrices
  LOG_PRINT(LOG_LEVEL_INFO, "Matrix generators");
  REGISTER_FACTORY_CLASS("StaticSynapticMatrix", MatrixGenerator, Static);
  REGISTER_FACTORY_CLASS("PlasticSynapticMatrix", MatrixGenerator, Plastic);
//  REGISTER_FACTORY_CLASS("ExtendedPlasticSynapticMatrix", MatrixGenerator, Plastic);

  // Register connector generators with factories
  LOG_PRINT(LOG_LEVEL_INFO, "Connector generators");
  REGISTER_FACTORY_CLASS("AllToAllConnector", ConnectorGenerator, AllToAll);
  REGISTER_FACTORY_CLASS("OneToOneConnector", ConnectorGenerator, OneToOne);
  REGISTER_FACTORY_CLASS("FixedProbabilityConnector", ConnectorGenerator,
                                                      FixedProbability);
  REGISTER_FACTORY_CLASS("KernelConnector", ConnectorGenerator, Kernel);
  REGISTER_FACTORY_CLASS("MappingConnector", ConnectorGenerator, Mapping);

  // REGISTER_FACTORY_CLASS("FixedTotalNumberConnector", ConnectorGenerator, FixedTotalNumber);

  // Register parameter generators with factories
  LOG_PRINT(LOG_LEVEL_INFO, "Parameter generators");
  REGISTER_FACTORY_CLASS("constant", ParamGenerator, Constant);
  REGISTER_FACTORY_CLASS("kernel",   ParamGenerator, ConvKernel);
  REGISTER_FACTORY_CLASS("uniform",  ParamGenerator, Uniform);
  REGISTER_FACTORY_CLASS("normal",   ParamGenerator, Normal);
//  REGISTER_FACTORY_CLASS("normal_clipped", ParamGenerator, NormalClipped);
//  REGISTER_FACTORY_CLASS("normal_clipped_to_boundary", ParamGenerator, NormalClippedToBoundary);
  REGISTER_FACTORY_CLASS("exponential", ParamGenerator, Exponential);

  // Allocate buffers for placement new from factories
  // **NOTE** we need to be able to simultaneously allocate a delay and
  // a weight generator so we need two buffers for parameter allocation
  g_MatrixGeneratorBuffer = g_MatrixGeneratorFactory.Allocate();
  g_ConnectorGeneratorBuffer = g_ConnectorGeneratorFactory.Allocate();
  g_DelayParamGeneratorBuffer = g_ParamGeneratorFactory.Allocate();
  g_WeightParamGeneratorBuffer = g_ParamGeneratorFactory.Allocate();

  // Get this core's base address using alloc tag
  // uint32_t *params_address = Config::GetBaseAddressAllocTag();
  LOG_PRINT(LOG_LEVEL_INFO, "%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

  LOG_PRINT(LOG_LEVEL_INFO, "Starting To Build Connectors");
  // If reading SDRAM data fails

  uint32_t *core_address = data_specification_get_data_address();
  uint32_t *sdram_address = data_specification_get_region(CONNECTOR_BUILDER_REGION,
                                                          core_address);
  uint32_t *syn_mtx_addr = data_specification_get_region(SYNAPTIC_MATRIX_REGION,
                                                         core_address);

  LOG_PRINT(LOG_LEVEL_INFO, "\tReading SDRAM at 0x%08x", sdram_address);

  if(!ReadSDRAMData(sdram_address, syn_mtx_addr))
  {
    LOG_PRINT(LOG_LEVEL_INFO, "!!!   Error reading SDRAM data   !!!");

    rt_error(RTE_ABORT);
    return;
  }

  LOG_PRINT(LOG_LEVEL_INFO, "Finished On Machine Connectors!");
//  spin1_delay_us(SLEEP_TIME);



  sark_cpu_state(CPU_STATE_EXIT);
  spin1_exit(0);


  return;
}



} // anonymous namespace

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void __cxa_pure_virtual()
{
  LOG_PRINT(LOG_LEVEL_ERROR, "Pure virtual function call");
}
//-----------------------------------------------------------------------------


extern "C" void c_main(void){
    LOG_PRINT(LOG_LEVEL_INFO, "%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    // kick-start the process
    spin1_schedule_callback(app_start, 0, 0, 2);
    spin1_callback_on(SDP_PACKET_RX, handle_sdp_message, 0);

    // go
    spin1_start(SYNC_NOWAIT); //##
} // end extern "C"
