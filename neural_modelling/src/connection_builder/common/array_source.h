#pragma once

// Rig CPP common includes
#include "rig_cpp_common/bit_field.h"
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/spinnaker.h"
#include "rig_cpp_common/utils.h"

// Common includes
#include "spike_recording.h"

// Namespaces
using namespace Common;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// Common::ArraySource
//-----------------------------------------------------------------------------
namespace Common
{
class ArraySource
{
public:
  //-----------------------------------------------------------------------------
  // Enumerations
  //-----------------------------------------------------------------------------
  enum DMATag
  {
    DMATagSpikeDataRead,
    DMATagMax,
  };

  ArraySource() : m_NextSpikeTick(0), m_SpikeBlockSizeWords(0),
    m_NextSpikeBlockAddress(NULL), m_DMABuffer(NULL), m_State(StateInactive)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons);
  bool DMATransferDone(uint tag);

  template<typename E>
  void Update(uint tick, E emitSpikeFunction, SpikeRecording &spikeRecording,
              unsigned int numNeurons)
  {
    // If we should be transmitting spikes this tick
    if(m_NextSpikeTick == tick)
    {
      // If there is data in the buffer
      if(m_State == StateSpikeBlockInBuffer)
      {
        // Loop through sources
        for(unsigned int s = 0; s < numNeurons; s++)
        {
          // If this source has spiked
          bool spiked = BitField::TestBit(&m_DMABuffer[1], s);
          if(spiked)
          {
            // Emit a spike
            LOG_PRINT(LOG_LEVEL_TRACE, "\tEmitting spike");
            emitSpikeFunction(s);
          }

          // Record spike
          spikeRecording.RecordSpike(s, spiked);
        }

        // Read next spike tick from start of block and
        // Advance offset to next block to fetch
        m_NextSpikeTick = m_DMABuffer[0];
        m_NextSpikeBlockAddress += m_SpikeBlockSizeWords;

        // Reset state
        m_State = StateInactive;

        LOG_PRINT(LOG_LEVEL_TRACE, "\tNext spike tick:%u", m_NextSpikeTick);
      }
      // Otherwise error
      else
      {
        LOG_PRINT(LOG_LEVEL_WARN, "DMA hasn't completed in time to transmit spikes at tick %u", tick);
      }
    }

    // If there are more spikes to send and we're inactive
    // (i.e. next block hasn't already been read)
    if(m_NextSpikeTick != UINT32_MAX && m_State == StateInactive)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tStarting DMA to read in spikes for tick %u from %08x",
                m_NextSpikeTick, m_NextSpikeBlockAddress);

      // Set state to DMA progress and start DMA
      m_State = StateDMAInProgress;

      // Start a DMA transfer from the absolute address of the spike block into buffer
      spin1_dma_transfer(DMATagSpikeDataRead, const_cast<uint32_t*>(m_NextSpikeBlockAddress),
        m_DMABuffer, DMA_READ, m_SpikeBlockSizeWords * sizeof(uint32_t));
    }
  }

private:
  //-----------------------------------------------------------------------------
  // Enumerations
  //-----------------------------------------------------------------------------
  enum State
  {
    StateInactive,
    StateDMAInProgress,
    StateSpikeBlockInBuffer,
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint m_NextSpikeTick;
  unsigned int m_SpikeBlockSizeWords;
  const uint32_t *m_NextSpikeBlockAddress;
  uint32_t *m_DMABuffer;
  State m_State;
};
} // namespace Common