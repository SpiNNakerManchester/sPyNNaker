#pragma once

// Standard includes
#include <functional>

// Rig CPP common includes
#include "rig_cpp_common/fixed_point_number.h"
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/spinnaker.h"
#include "rig_cpp_common/utils.h"
#include "rig_cpp_common/random/non_uniform.h"

// Common includes
#include "spike_recording.h"

// Namespaces
using namespace Common::FixedPointNumber;
using namespace Common::Random;
using namespace Common;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// Common::PoissonSource
//-----------------------------------------------------------------------------
namespace Common
{
template <typename R>
class PoissonSource
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // Poisson source doesn't use any DMA tags
  static const uint DMATagMax = 0;

  PoissonSource() : m_ImmutableState(NULL), m_ImmutableStateIndices(NULL), m_SlowTimeToSpike(NULL)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numSources)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "PoissonSource::ReadSDRAMData");

    // Read RNG seed
    uint32_t seed[R::StateSize];
    LOG_PRINT(LOG_LEVEL_TRACE, "\tSeed:");
    for(unsigned int s = 0; s < R::StateSize; s++)
    {
      seed[s] = *region++;
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u", seed[s]);
    }
    m_RNG.SetState(seed);

    LOG_PRINT(LOG_LEVEL_TRACE, "\tPoisson spike source immutable state");
    if(!AllocateCopyIndexedStructArray(numSources, region,
      m_ImmutableStateIndices, m_ImmutableState))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate spike source immutable state array");
      return false;
    }

    // Allocate time to spike array
    // **NOTE** this is only USED by slow spike sources but
    // for simplicity we allocate one for each neuron
    m_SlowTimeToSpike = (S1615*)spin1_malloc(sizeof(S1615) * numSources);

    // Loop through spike sources
    S1615 *tts = m_SlowTimeToSpike;
    const uint16_t *immutableStateIndex = m_ImmutableStateIndices;
    for(unsigned int s = 0; s < numSources; s++)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tSimulating spike source %u", s);

      // Get mutable and immutable state for spike source
      auto &sourceTTS = *tts++;
      auto &sourceImmutableState = m_ImmutableState[*immutableStateIndex++];

      // Initialize spike source
      sourceImmutableState.Initialize(sourceTTS, m_RNG);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
      sourceImmutableState.Print(IO_BUF, sourceTTS);
#endif
    }

    return true;
  }

  bool DMATransferDone(uint)
  {
    return false;
  }

  template<typename E>
  void Update(uint tick, E emitSpikeFunction, SpikeRecording &spikeRecording,
              unsigned int numSources)
  {
    // Loop through spike sources
    auto *tts = m_SlowTimeToSpike;
    const uint16_t *immutableStateIndex = m_ImmutableStateIndices;
    for(unsigned int s = 0; s < numSources; s++)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tSimulating spike source %u", s);

      // Get mutable and immutable state for spike source
      auto &sourceTTS = *tts++;
      const auto &sourceImmutableState = m_ImmutableState[*immutableStateIndex++];

      // Bind source ID to emit spike function
      auto sourceEmitSpikeFunction = std::bind(emitSpikeFunction, s);

      // Update spike
      const bool spiked = sourceImmutableState.Update(tick, sourceTTS, m_RNG, sourceEmitSpikeFunction);
      spikeRecording.RecordSpike(s, spiked);
    }
  }

private:
  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  class ImmutableState
  {
  public:
    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    void Print(char *stream, S1615 slowTimeToSpike) const
    {
      io_printf(stream, "\tImmutable state:\n");
      io_printf(stream, "\t\tStartTick      = %u\n", m_StartTick);
      io_printf(stream, "\t\tEndTick        = %u\n", m_EndTick);
      if(IsSlow())
      {
        io_printf(stream, "\t\tMeanISI        = %k\n", m_Data.m_MeanISI);

        io_printf(stream, "\tMutable state:\n");
        io_printf(IO_BUF, "\t\tTTS            = %k\n", slowTimeToSpike);
      }
      else
      {
        io_printf(stream, "\t\tExpMinusLambda = %k\n", (S1615)(m_Data.m_ExpMinusLambda >> 17));
      }
    }

    template<typename E>
    bool Update(uint tick, S1615 &slowTimeToSpike, R &rng, E emitSpikeFunction) const
    {
      // If spike source is active, return result of correct update function
      if((tick >= m_StartTick) && (tick < m_EndTick))
      {
        if(IsSlow())
        {
          return UpdateSlow(slowTimeToSpike, rng, emitSpikeFunction);
        }
        else
        {
          return UpdateFast(rng, emitSpikeFunction);
        }
      }
      // Otherwise, return false
      else
      {
        return false;
      }
    }

    void Initialize(S1615 &slowTimeToSpike, R &rng) const
    {
      // If this is a slow spike source, calculate the initial time to spike
      if(IsSlow())
      {
        slowTimeToSpike = CalculateTTS(rng);
      }
    }

  private:
    //-----------------------------------------------------------------------------
    // Unions
    //-----------------------------------------------------------------------------
    union TypeSpecificData
    {
      S1615 m_MeanISI;
      U032 m_ExpMinusLambda;
    };

    //-----------------------------------------------------------------------------
    // Private methods
    //-----------------------------------------------------------------------------
    bool IsSlow() const
    {
      return (m_IsSlow != 0);
    }

    S1615 CalculateTTS(R &rng) const
    {
      return MulS1615(m_Data.m_MeanISI, NonUniform::ExponentialDistVariate(rng));
    }

    template<typename E>
    bool UpdateSlow(S1615 &tts, R &rng, E emitSpikeFunction) const
    {
      // If it's time to spike
      const bool spiked = (tts <= 0);
      if(spiked)
      {
        // Update time-to-spike
        S1615 nextTTS = CalculateTTS(rng);
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tNext time-to-spike:%k ticks", nextTTS);
        tts += nextTTS;

        // Call emit spike function
        emitSpikeFunction();
      }

      // Subtract one
      tts -= S1615One;

      // Return whether spikes have been emitted
      return spiked;
    }

    template<typename E>
    bool UpdateFast(R &rng, E emitSpikeFunction) const
    {
      // Get number of spikes to emit this timestep
      unsigned int numSpikes = NonUniform::PoissonDistVariate(rng, m_Data.m_ExpMinusLambda);
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEmitting %u spikes", numSpikes);

      // Emit spikes
      for(unsigned int s = 0; s < numSpikes; s++)
      {
        emitSpikeFunction();
      }

      // Return true if any spikes have been emitted
      return (numSpikes > 0);
    }

    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    uint32_t m_IsSlow;
    uint32_t m_StartTick;
    uint32_t m_EndTick;
    TypeSpecificData m_Data;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  ImmutableState *m_ImmutableState;
  uint16_t *m_ImmutableStateIndices;
  S1615 *m_SlowTimeToSpike;

  R m_RNG;
};
} // Common