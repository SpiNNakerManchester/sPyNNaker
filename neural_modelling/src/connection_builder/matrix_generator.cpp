#include "matrix_generator.h"

// Standard includes
#include <algorithm>

// Rig CPP common includes
#include "rig_cpp_common/log.h"

// Connection builder includes
#include "connector_generator.h"
#include "param_generator.h"

//#define DEBUG_MESSAGES
#define MAX_DELAY 16

#define _pack_id_delay(i, d) ((i & 0xFF) | ((d & 0xFF) << 8))

// **YUCK** standard algorithms tend to rely on memcpy under the hood.
// This wraps the SpiNNaker memcpy routine in a suitable form
// it probably belongs somewhere else though
void* memcpy(void* dest, const void* src, std::size_t count)
{
  spin1_memcpy(dest, src, count);
  return dest;
}

inline uint32_t to_shifted_fix88(uint32_t fix1616, uint32_t shift){
//  uint32_t fix88 = (fix1616 >> (16 - shift)) ;
  uint32_t fix88 = (fix1616 >> 16) ;
  return fix88;
}


//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Base
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Base::Base(uint32_t *&region){
  m_SignedWeight = *region++;
  m_PreStateWords = *region++;

}
//-----------------------------------------------------------------------------
bool ConnectionBuilder::MatrixGenerator::Base::Generate(
  uint32_t *synaptic_matrix_address,   uint32_t address_delta,
  uint32_t max_num_static, uint32_t max_num_plastic,
  uint32_t max_per_pre_matrix_size,  uint32_t synapse_type,
  uint32_t post_start, uint32_t post_count, 
  uint32_t pre_key,    uint32_t pre_mask,
  uint32_t pre_start,  uint32_t pre_count,
  uint32_t pre_block_start,  uint32_t pre_block_count,
  uint32_t num_pre_neurons, uint32_t words_per_weight,
  int32_t *scales,  uint32_t syn_type_bits,
  ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng, uint16_t *pre_delay_pairs, uint16_t &pair_count) const{

#ifdef DEBUG_MESSAGES
    LOG_PRINT(LOG_LEVEL_INFO,
             "\tGenerating (%u, %u)(%u:%u) => (%u:%u)",
              pre_start, pre_start+pre_count-1,
              pre_block_start, pre_block_start+pre_block_count-1,
              post_start, post_start+post_count-1);
#endif
//    LOG_PRINT(LOG_LEVEL_INFO, "words per weight %d", words_per_weight);

    uint32_t max_indices = max_num_plastic + max_num_static;
    pair_count = 0;

    uint32_t *ind_syn_mtx = synaptic_matrix_address + 1;
    uint32_t total_conns = 0;
    for(uint32_t pre_idx = pre_block_start; pre_idx < (pre_block_start + pre_block_count);
        pre_idx++){

//    for(uint16_t pre_idx = pre_start; pre_idx < pre_start + pre_count; pre_idx++){
      uint16_t indices[512];
#ifdef DEBUG_MESSAGES
       LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\tGenerating indices-------------------------");
#endif
      const uint32_t numIndices = connectorGenerator->Generate(
                                            pre_block_start, pre_block_count,
                                            pre_idx,
                                            post_start, post_count,
                                            max_indices, rng, indices);
//#ifdef DEBUG_MESSAGES
//       LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\t%u indices", numIndices);
//#endif

      // TraceUInt(indices, numIndices);

      // Generate delays for each index
      int32_t delays[512];
//#ifdef DEBUG_MESSAGES
//       LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\tGenerating delays-------------------------");
//#endif
      delayGenerator->Generate(numIndices, 0, pre_idx, post_start, indices,
                               rng, delays);
      // TraceUInt(delays, numIndices);

      // Generate weights for each index
      int32_t weights[512];
//#ifdef DEBUG_MESSAGES
//       LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\tGenerating weights------------------------");
//#endif
      // STATIC == 0, PLASTIC == 1
      weightGenerator->Generate(numIndices, scales[synapse_type],
                                pre_idx, post_start, indices,
                                rng, weights);
      // TraceUInt(weights, numIndices);


      for(uint32_t idx = 0; idx < numIndices; idx++ ){
        pre_delay_pairs[pair_count] = 0;
        uint32_t d = ClampDelay(delays[idx]);
        if(d > MAX_DELAY){
//            LOG_PRINT(LOG_LEVEL_INFO, "pre = %u, delay = %u", pre_idx, d);
            pre_delay_pairs[pair_count] = _pack_id_delay(pre_idx, d);
            pair_count++;
        }

      }

//      pre_idx += pre_start;

      // Write row
      unsigned int rowWords = WriteRow(ind_syn_mtx + address_delta,
//                               num_pre_neurons,
                               pre_count,
                               pre_idx-pre_start, max_per_pre_matrix_size,
                               numIndices, 0, syn_type_bits, words_per_weight,
//                               numIndices, scales[synapse_type], syn_type_bits,
                               max_num_plastic, max_num_static, synapse_type,
                               indices, delays, weights);

#ifdef DEBUG_MESSAGES
      if(pre_idx%1 == 0 && numIndices > 0){
        LOG_PRINT(LOG_LEVEL_INFO, "\t\tGenerated %u synapses for %u, addr delta %u",
                  numIndices, pre_idx, address_delta);
      }
#endif
      total_conns += numIndices;
    }
#ifdef DEBUG_MESSAGES

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tTotal synapses generated = %u . Done!",
            total_conns);
#endif

  //TODO: add support for direct matrices
  //direct synapse matrix not supported yet!
  *(synaptic_matrix_address + (*synaptic_matrix_address >> 2) + 1) = 0;
  return true;
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Base::TraceUInt(uint32_t (&values)[512],
                                                         unsigned int number) const
{
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < number; i++)
  {
    io_printf(IO_BUF, "%u,", values[i]);
  }
  io_printf(IO_BUF, "\n");
#endif
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Base::TraceInt(int32_t (&values)[512],
                                                        unsigned int number) const
{
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < number; i++)
  {
    io_printf(IO_BUF, "%d,", values[i]);
  }
  io_printf(IO_BUF, "\n");
#endif
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Static
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Static::Static(uint32_t *&region) : Base(region)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tStatic synaptic matrix: %u signed weights",
    IsSignedWeight());
  is_static = true;
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::MatrixGenerator::Static::WriteRow(uint32_t *synapse_mtx,
  uint32_t num_pre_neurons, uint32_t pre_idx, const uint32_t max_per_pre_matrix_size,
  const uint32_t numIndices, const int32_t weight_shift,
  uint32_t syn_type_bits, uint32_t words_per_weight,
  const uint32_t max_num_plastic, const uint32_t max_num_static, uint32_t synapseType,
  const uint16_t (&indices)[512], const int32_t (&delays)[512], const int32_t (&weights)[512]) const {
//  LOG_PRINT(LOG_LEVEL_INFO, "Static Writer");
  uint32_t fixed_mask = ((1 << (syn_type_bits + SYNAPSE_INDEX_BITS)) - 1);
  uint32_t inserted_indices = 0;
  uint32_t max_plastic_words = max_num_plastic/2 + max_num_plastic%2;
  uint32_t min_indices = max_num_static < numIndices ? max_num_static : numIndices;
  uint8_t first_pass = 1;
  uint32_t preIndex = pre_idx;


  for(uint16_t data_index = 0; data_index < numIndices; data_index++){
    // Extract index pointed to by sorted index
    const uint32_t postIndex = indices[data_index];

    // EXC == 0, INH == 1
    int32_t weight = weights[data_index];

//    if(weight == 0){ continue; }

//    LOG_PRINT(LOG_LEVEL_INFO, "pre, post, w => %u, %u, %k",
//              pre_idx, postIndex, weight);

    if (IsSignedWeight() && weight < 0 &&
        (synapseType == 0 || synapseType == 1)){
      synapseType = 1;
      weight = -weight;
    }
    weight = ClampWeight(weight);

    // Clamp delays and weights pointed to be sorted index
    int32_t delay = ClampDelay(delays[data_index]);

    if(delay > MAX_DELAY){

        uint32_t delay_shift = 1;
        if(delay%MAX_DELAY == 0){ delay_shift++; }

        preIndex = pre_idx + (delay/MAX_DELAY - delay_shift)*num_pre_neurons;
    }
    delay = delay%MAX_DELAY;

    // Build synaptic word
    uint32_t word = BuildStaticWord(weight, delay, synapseType, postIndex, syn_type_bits);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    io_printf(IO_BUF, "%u,", word);
#endif

    uint32_t *start_of_submatrix = synapse_mtx + 1 + preIndex*(max_per_pre_matrix_size);

    uint32_t *start_of_static = start_of_submatrix + max_plastic_words;


//    TODO: should I set this?
    if( first_pass ){
//      *start_of_static = *start_of_static + max_num_static;
      //how many indices where generated on machine
      *start_of_static = *start_of_static + min_indices;
      if(*start_of_static > max_num_static){
        *start_of_static = max_num_static;
      }
//    *start_of_static = max_num_static;
    }


    start_of_static += 2;

    // Write word to matrix
    //0 <- plastic-plastic word
    //NULL <- start of plastic-plastic region,
    //false <- not a plastic synapse
    insert_sorted(word, start_of_static, fixed_mask, max_num_static,
                  0, NULL, 1, false, false);
    first_pass = 0;
    inserted_indices++;
    if(inserted_indices == max_num_static){
      break;
    }
  }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
  io_printf(IO_BUF, "\n");
#endif

  // Return number of words written to row
  return 1;
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::MatrixGenerator::Static::GetMaxRowWords(unsigned int maxRowSynapses) const
{
  return maxRowSynapses;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Plastic
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Plastic::Plastic(uint32_t *&region) : Base(region)
{
  // // Read number of presynaptic state words from region
  // const uint32_t preStateBytes = *region++;
  // m_SynapseTraceBytes = *region++;
  is_static = false;
  // // Round up to words
  LOG_PRINT(LOG_LEVEL_INFO,
        "\t\tPlastic synapse matrix: signed weights %u, num synapse pre-trace words %u",
        IsSignedWeight(), m_PreStateWords);

  // LOG_PRINT(LOG_LEVEL_INFO, "\t\tPlastic synaptic matrix: %u signed weights, %u bytes presynaptic state (%u words), %u bytes synapse trace",
  //           IsSignedWeight(), preStateBytes, m_PreStateWords, m_SynapseTraceBytes);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::MatrixGenerator::Plastic::WriteRow(uint32_t *synapse_mtx,
  uint32_t num_pre_neurons, uint32_t pre_idx, const uint32_t max_per_pre_matrix_size,
  const uint32_t numIndices, const int32_t weight_shift,
  uint32_t syn_type_bits, uint32_t words_per_weight,
  const uint32_t max_num_plastic, const uint32_t max_num_static, uint32_t synapseType,
  const uint16_t (&indices)[512], const int32_t (&delays)[512], const int32_t (&weights)[512]) const {

  uint16_t fixed_mask = ((1 << (syn_type_bits + SYNAPSE_INDEX_BITS)) - 1);
#ifdef DEBUG_MESSAGES
  LOG_PRINT(LOG_LEVEL_INFO, "Plastic Writer");
  LOG_PRINT(LOG_LEVEL_INFO, "synapse type bits %u", syn_type_bits);
#endif

  uint16_t inserted_indices = 0;
//  uint32_t plastic_step = m_PreStateWords + numIndices;
  uint32_t preIndex = pre_idx;
  bool first_pass = true;

  uint32_t max_plastic_words = max_num_plastic/2 + max_num_plastic%2;
  uint32_t min_indices = max_num_plastic < numIndices ? max_num_plastic : numIndices;
  uint32_t min_ind_words = min_indices/2 + min_indices%2;

  uint16_t data_index = 0;
  bool inserted_empty = false;
//  LOG_PRINT(LOG_LEVEL_INFO, "before do-while loop");
  do{

    // Extract index pointed to by sorted index
    const uint32_t postIndex = indices[data_index];

    // EXC == 0, INH == 1
    int16_t weight = weights[data_index];
    if (IsSignedWeight() && weight < 0 &&
        (synapseType == 0 || synapseType == 1)){
      synapseType = 1;
    }
    if (IsSignedWeight() && weight < 0){
      weight = -weight;
    }

    weight = ClampWeight(weight);

    // Clamp delays and weights pointed to be sorted index
    int32_t delay = ClampDelay(delays[data_index]);

    if(delay > 16){
      uint32_t delay_shift = 1;
      if(delay%MAX_DELAY == 0){ delay_shift++; }
      preIndex = pre_idx + (delay/MAX_DELAY - delay_shift)*num_pre_neurons;
    }
    delay = delay%16;

    uint32_t *start_of_matrix = synapse_mtx + preIndex*max_per_pre_matrix_size;

    *start_of_matrix = m_PreStateWords + min_indices;

    uint16_t *start_of_fixed = (uint16_t *)(start_of_matrix + m_PreStateWords +
                                            min_indices + max_num_static + 2);
    uint16_t *start_of_plastic = (uint16_t *)(start_of_matrix + m_PreStateWords + 1);

#ifdef DEBUG_MESSAGES
    LOG_PRINT(LOG_LEVEL_INFO, "Start of syn_mtx = 0x%08x", synapse_mtx);
    LOG_PRINT(LOG_LEVEL_INFO, "Start of Matrix = 0x%08x", start_of_matrix);
    LOG_PRINT(LOG_LEVEL_INFO, "Start of Plastic = 0x%08x", start_of_plastic);
    LOG_PRINT(LOG_LEVEL_INFO, "Start of Fixed = 0x%08x", start_of_fixed);
    LOG_PRINT(LOG_LEVEL_INFO, "Max per Pre Matrix Size = %u", max_per_pre_matrix_size);
#endif


    const uint16_t fixed = BuildFixedPlasticWord(0, // axonal delay <- not implemented
                                                 delay, // dendritic delay
                                                 synapseType, postIndex,
                                                 0, // axon_bits
                                                 4, // dendrite_bits
                                                 syn_type_bits);

//    LOG_PRINT(LOG_LEVEL_INFO, "after build fixed-plastic");
    // Write word to matrix
    //0 <- plastic-plastic word
    //NULL <- start of plastic-plastic region,
    //false <- not a plastic synapse
    //0 <- plastic row size in words
//    LOG_PRINT(LOG_LEVEL_INFO, "Stored num of plastic 32-bit words = %u",
//              *synapse_mtx);
    if(first_pass){
      *start_of_fixed = *start_of_fixed + numIndices;
      if(*start_of_fixed > max_num_plastic){
        *start_of_fixed = max_num_plastic;
      }

    }
    start_of_fixed += 2;
//    LOG_PRINT(LOG_LEVEL_INFO, "before if numIndices");
    if(numIndices > 0){
//      LOG_PRINT(LOG_LEVEL_INFO, "before insert sorted");
      insert_sorted(fixed, start_of_fixed, fixed_mask, max_num_plastic, weight,
                    start_of_plastic, words_per_weight, true, inserted_empty);
//      LOG_PRINT(LOG_LEVEL_INFO, "after insert sorted");

      if(fixed == EMPTY_VAL){
        inserted_empty = true;
      }
    } else{
//        LOG_PRINT(LOG_LEVEL_INFO, "num indices == 0");
        return 0;
    }
    first_pass = false;
    inserted_indices++;
    data_index++;

    if(inserted_indices == max_num_plastic){
      break;
    }

  }while(data_index < numIndices);
  return 0;
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::MatrixGenerator::Plastic::GetMaxRowWords(unsigned int maxRowSynapses) const
{
  return m_PreStateWords + GetNumPlasticWords(maxRowSynapses) + GetNumControlWords(maxRowSynapses);
}
