#pragma once

// Standard include
#include <algorithm>
#include <cstdint>

// Common includes
#include "./common/row_offset_length.h"

// Connection builder includes
#include "generator_factory.h"

// Forward declarations
namespace Common
{
  namespace Random
  {
    class MarsKiss64;
  }
}

// Namespaces
using namespace Common::Random;

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
// Forward declarations
namespace ConnectorGenerator
{
  class Base;
}

namespace ParamGenerator
{
  class Base;
}

namespace MatrixGenerator
{

//! how many bits the synapse weight will take
#ifndef SYNAPSE_WEIGHT_BITS
#define SYNAPSE_WEIGHT_BITS 16
#endif

//! how many bits the synapse delay will take
#ifndef SYNAPSE_DELAY_BITS
#define SYNAPSE_DELAY_BITS 4
#endif

//! how many bits the synapse can support to represent the neuron id.
#ifndef SYNAPSE_INDEX_BITS
#define SYNAPSE_INDEX_BITS 8
#endif

// Create some masks based on the number of bits
#define SYNAPSE_WEIGHT_MASK     ((1 << SYNAPSE_WEIGHT_BITS) - 1)
//! the mask for the synapse delay in the row
#define SYNAPSE_DELAY_MASK      ((1 << SYNAPSE_DELAY_BITS)  - 1)
#define SYNAPSE_INDEX_MASK      ((1 << SYNAPSE_INDEX_BITS)  - 1)

#define EMPTY_VAL 0

//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  Base(uint32_t *&region);
  uint32_t m_PreStateWords; //TODO: should make this private + accessors
  uint32_t m_WordsPerWeight;
  bool is_static;
  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool Generate(uint32_t *synaptic_matrix_address, uint32_t address_delta,
                uint32_t max_num_static,
                uint32_t max_num_plastic, uint32_t max_per_pre_matrix_size,
                uint32_t synapse_type, uint32_t post_start, uint32_t post_count, 
                uint32_t pre_key, uint32_t pre_mask,
                uint32_t pre_start, uint32_t pre_count,
                uint32_t pre_block_start,  uint32_t pre_block_end,
                uint32_t num_pre_neurons, uint32_t words_per_weight,
                int32_t* weight_scales, uint32_t syn_type_bits,
                ConnectorGenerator::Base *connectorGenerator,
                const ParamGenerator::Base *delayGenerator,
                const ParamGenerator::Base *weightGenerator, MarsKiss64 &rng,
                uint16_t *pre_delay_pairs, uint16_t &pair_count) const;

protected:
  template <typename T>
  void swap(T &val1, T &val2) const{
    T tmp = val1;
    val1 = val2;
    val2 = tmp;
  }

  template <typename T>
  void insert_sorted(T new_fixed, T *fixed_address, T val_mask, uint32_t max_rows,
                     uint16_t new_plastic=0, uint16_t *plastic_address=NULL,
                     uint32_t plastic_step=1,
                     bool is_plastic=false, bool skip_first=false) const{

      if (*fixed_address == EMPTY_VAL && !skip_first){
        *fixed_address = new_fixed;

        if(is_plastic){ plastic_address[plastic_step-1] = new_plastic; }
        return;
      }
      for(uint32_t i = 1; i < max_rows; i++){
        if ((fixed_address[i] == EMPTY_VAL) && \
           (fixed_address[i - 1] & val_mask) < \
           (new_fixed & val_mask)){

            fixed_address[i] = new_fixed;

            if(is_plastic){
              plastic_address[plastic_step*(i+1) - 1] = new_plastic;
            }
//            LOG_PRINT(LOG_LEVEL_INFO, "\tinserted in %u", i);
            return;
        }
        else if ((fixed_address[i] == EMPTY_VAL) && \
                 (fixed_address[i - 1] & val_mask) > \
                 (new_fixed & val_mask)){

          fixed_address[i] = fixed_address[i - 1];
          fixed_address[i - 1] = new_fixed;

          if(is_plastic){
            plastic_address[plastic_step*(i+1) - 1] = \
                                plastic_address[plastic_step*i - 1];
            plastic_address[plastic_step*i - 1] = new_plastic;
          }
//          LOG_PRINT(LOG_LEVEL_INFO, "\tinserted in %u", i);
          return;
        }
        else if ((fixed_address[i - 1] & val_mask) > \
                 (new_fixed & val_mask)){

          swap(fixed_address[i-1], new_fixed);
          if(is_plastic){
            swap(plastic_address[plastic_step*(i - 1)], new_plastic);
          }
        }
      }

  }

  uint16_t BuildFixedPlasticWord(const uint32_t axon_delay,
                                 const uint32_t dendrite_delay,
                                 const uint32_t type, const uint16_t post_index,
                                 const uint32_t axon_bits,
                                 const uint32_t dendrite_bits,
                                 const uint32_t syn_type_bits)const {
    uint32_t shift = 0;
    uint16_t wrd  = (post_index & SYNAPSE_INDEX_MASK);

    shift = SYNAPSE_INDEX_BITS;
    wrd |= ((type & ((1 << syn_type_bits) - 1)) << shift);

    shift += syn_type_bits;
    wrd |= ((dendrite_delay & ((1 << dendrite_bits) - 1) ) << shift);

    shift += dendrite_bits;
    wrd |= ((axon_delay & ((1 << axon_bits)) ) << shift);

    return wrd;
  }


  uint32_t BuildStaticWord(const uint32_t weight, const uint32_t delay,
                           const uint32_t type, const uint16_t post_index,
                           const uint32_t syn_type_bits) const{
//    LOG_PRINT(LOG_LEVEL_INFO, "idx %u, type %u, delay %u, weight %u",
//              post_index & (( 1 << neuron_id_bits) - 1),
//              (type & ((1 << syn_type_bits) - 1)), (delay & SYNAPSE_DELAY_MASK),
//               weight & SYNAPSE_WEIGHT_MASK);
    uint32_t wrd  = (post_index & SYNAPSE_INDEX_MASK);
             wrd |= ((type & ((1 << syn_type_bits) - 1)) << SYNAPSE_INDEX_BITS);
             wrd |= ((delay & SYNAPSE_DELAY_MASK) << (SYNAPSE_INDEX_BITS + syn_type_bits));
             wrd |= ((weight & SYNAPSE_WEIGHT_MASK) << (32 - SYNAPSE_WEIGHT_BITS));
    return wrd;
  }
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int WriteRow(uint32_t *synapse_mtx, uint32_t num_pre_neurons,
  uint32_t pre_idx, const uint32_t max_per_pre_matrix_size, const uint32_t numIndices,
  const int32_t weight_shift,  uint32_t syn_type_bits, uint32_t words_per_weight,
  const uint32_t max_num_plastic, const uint32_t max_num_static, uint32_t synapseType,
  const uint16_t (&indices)[512], const int32_t (&delays)[512], const int32_t (&weights)[512]) const = 0;

  virtual unsigned int GetMaxRowWords(unsigned int maxRowSynapses) const = 0;

  //-----------------------------------------------------------------------------
  // Protected methods
  //-----------------------------------------------------------------------------
  void TraceUInt(uint32_t (&values)[512], unsigned int number) const;
  void TraceInt(int32_t (&values)[512], unsigned int number) const;

  int32_t ClampWeight(int32_t weight) const
  {
//    if(IsSignedWeight())
//    {
//      return std::max<int32_t>(INT16_MIN,
//                               std::min<int32_t>(INT16_MAX, weight));
//    }
//    // Otherwise, if weights aren't signed and weight is negative, zero
//    // **NOTE** negative weights caused by inhibitory
//    // weights should have been already flipped in host
//    else
//    {
      return std::max<int32_t>(0,
                               std::min<int32_t>(UINT16_MAX, weight));
//    }
  }

  int32_t ClampDelay(int32_t delay) const
  {
    // If delay is lower than minimum (1 timestep), clamp
    return (delay < 1) ? 1 : delay;
  }

  bool IsSignedWeight() const{ return (m_SignedWeight != 0); }


  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t DelayBits = 3;
  static const uint32_t IndexBits = 10;
  static const uint32_t DelayMask = ((1 << DelayBits) - 1);
  static const uint32_t IndexMask = ((1 << IndexBits) - 1);

  static const uint32_t NumHeaderWords = 3;
  static const uint32_t MaxDTCMDelaySlots = 7;

  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef Common::RowOffsetLength<IndexBits> RowOffsetLength;

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_SignedWeight;
};

//-----------------------------------------------------------------------------
// Static
//-----------------------------------------------------------------------------
class Static : public Base
{
public:
  ADD_FACTORY_CREATOR(Static);

protected:
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int WriteRow(uint32_t *synapse_mtx, uint32_t num_pre_neurons,
  uint32_t pre_idx, const uint32_t max_per_pre_matrix_size, const uint32_t numIndices,
  const int32_t weight_shift,  uint32_t syn_type_bits, uint32_t words_per_weight,
  const uint32_t max_num_plastic, const uint32_t max_num_static, uint32_t synapseType,
  const uint16_t (&indices)[512], const int32_t (&delays)[512], const int32_t (&weights)[512]) const;

  virtual unsigned int GetMaxRowWords(unsigned int maxRowSynapses) const;

private:
  Static(uint32_t *&region);
};

//-----------------------------------------------------------------------------
// Plastic
//-----------------------------------------------------------------------------
class Plastic : public Base
{
public:
  ADD_FACTORY_CREATOR(Plastic);

protected:
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int WriteRow(uint32_t *synapse_mtx, uint32_t num_pre_neurons,
  uint32_t pre_idx, const uint32_t max_per_pre_matrix_size, const uint32_t numIndices,
  const int32_t weight_shift, uint32_t syn_type_bits, uint32_t words_per_weight,
  const uint32_t max_num_plastic, const uint32_t max_num_static, uint32_t synapseType,
  const uint16_t (&indices)[512], const int32_t (&delays)[512], const int32_t (&weights)[512]) const;

  virtual unsigned int GetMaxRowWords(unsigned int maxRowSynapses) const;

private:
  Plastic(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Private methods
  //-----------------------------------------------------------------------------
  unsigned int GetNumPlasticWords(unsigned int numSynapses) const
  {
    // Calculate the size of the plastic part of row
    const unsigned int numPlasticArrayBytes = numSynapses * (2 + m_SynapseTraceBytes);

    return (numPlasticArrayBytes / 4) + (((numPlasticArrayBytes & 3) != 0) ? 1 : 0);
  }

  unsigned int GetNumControlWords(unsigned int numSynapses) const
  {
    // Calculate the size of the control part of row
    return (numSynapses / 2) + (((numSynapses & 1) != 0) ? 1 : 0);
  }
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_SynapseTraceBytes;

};
} // MatrixGenerator
} // ConnectionBuilder
