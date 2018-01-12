#pragma once

// Standard includes
#include <cstdint>

// Connection builder includes
#include "generator_factory.h"
#include "kernel_maths.h"

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
// ConnectionBuilder::ConnectorGenerators
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace ConnectorGenerator
{

//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
                                uint32_t pre_idx,
                                uint32_t post_start, uint32_t post_count,
                                uint32_t max_indices,
                                MarsKiss64 &rng, uint16_t (&indices)[512]) = 0;

};

class Kernel : public Base{
  public:
    ADD_FACTORY_CREATOR(Kernel);
    virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
                                uint32_t pre_idx,
                                uint32_t post_start, uint32_t post_count,
                                uint32_t max_indices,
                                MarsKiss64 &rng, uint16_t (&indices)[512]);

  private:
    Kernel(uint32_t *&);
    uint16_t m_commonHeight;
    uint16_t m_commonWidth;

    uint16_t m_preHeight;
    uint16_t m_preWidth;
    uint16_t m_postHeight;
    uint16_t m_postWidth;

    uint16_t m_startPreHeight;
    uint16_t m_startPreWidth;
    uint16_t m_startPostHeight;
    uint16_t m_startPostWidth;

    uint16_t  m_stepPreWidth;
    uint16_t  m_stepPreHeight;
    uint16_t  m_stepPostWidth;
    uint16_t  m_stepPostHeight;

    uint16_t  m_kernelWidth;
    uint16_t  m_kernelHeight;

};

class Mapping : public Base{
  public:
    ADD_FACTORY_CREATOR(Mapping);
    virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
                                uint32_t pre_idx,
                                uint32_t post_start, uint32_t post_count,
                                uint32_t max_indices,
                                MarsKiss64 &rng, uint16_t (&indices)[512]);

  private:
    Mapping(uint32_t *&);
    uint16_t m_height;
    uint16_t m_width;
    uint8_t m_channel;
    uint8_t m_eventBits;
    uint8_t m_heightBits;
    uint8_t m_channelBits;

};

//-----------------------------------------------------------------------------
// AllToAll
//-----------------------------------------------------------------------------
class AllToAll : public Base
{
public:
  ADD_FACTORY_CREATOR(AllToAll);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
                                uint32_t pre_idx,
                                uint32_t post_start, uint32_t post_count,
                                uint32_t max_indices,
                                MarsKiss64 &rng, uint16_t (&indices)[512]);

private:
  AllToAll(uint32_t *&);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_AllowSelfConnections;
};

//-----------------------------------------------------------------------------
// OneToOne
//-----------------------------------------------------------------------------
class OneToOne : public Base
{
public:
  ADD_FACTORY_CREATOR(OneToOne);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
                                uint32_t pre_idx,
                                uint32_t post_start, uint32_t post_count,
                                uint32_t max_indices,
                                MarsKiss64 &rng, uint16_t (&indices)[512]);

private:
  OneToOne(uint32_t *&);
};

//-----------------------------------------------------------------------------
// FixedProbability
//-----------------------------------------------------------------------------
 class FixedProbability : public Base
 {
 public:
   ADD_FACTORY_CREATOR(FixedProbability);

   //-----------------------------------------------------------------------------
   // Base virtuals
   //-----------------------------------------------------------------------------
   virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
                                uint32_t pre_idx,
                                uint32_t post_start, uint32_t post_count,
                                uint32_t max_indices,
                                MarsKiss64 &rng, uint16_t (&indices)[512]);

 private:
   FixedProbability(uint32_t *&region);

   //-----------------------------------------------------------------------------
   // Members
   //-----------------------------------------------------------------------------
   uint32_t m_Probability;
   uint32_t m_AllowSelfConnections;
 };


// //-----------------------------------------------------------------------------
// // FixedTotalNumber
// //-----------------------------------------------------------------------------
// class FixedTotalNumber : public Base
// {
// public:
//   ADD_FACTORY_CREATOR(FixedTotalNumber);

//   //-----------------------------------------------------------------------------
//   // Base virtuals
//   //-----------------------------------------------------------------------------
//   virtual unsigned int Generate(uint32_t pre_start, uint32_t pre_count,
//                                 uint32_t post_start, uint32_t post_count,
//                                 uint32_t post_idx,
//                                 MarsKiss64 &rng, uint16_t (&indices)[512]);

// private:
//   FixedTotalNumber(uint32_t *&region);

//   //-----------------------------------------------------------------------------
//   // Members
//   //-----------------------------------------------------------------------------
//   uint32_t m_AllowSelfConnections;
//   uint32_t m_WithReplacement;
//   uint32_t m_ConnectionsInSubmatrix;
//   uint32_t m_SubmatrixSize;
// };

} // ConnectorGenerators
} // ConnectionBuilder
