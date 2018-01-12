#include "array_source.h"

// Rig CPP common includes
#include "rig_cpp_common/spinnaker.h"

//-----------------------------------------------------------------------------
// Common::ArraySource
//-----------------------------------------------------------------------------
namespace Common
{
bool ArraySource::ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons)
{
  LOG_PRINT(LOG_LEVEL_INFO, "ArraySource::ReadSDRAMData");

  // Read the time of the next spike block and store pointer to the start of the spike data region
  m_NextSpikeTick = (uint)region[0];
  m_NextSpikeBlockAddress = &region[1];

  // Allocate DMA buffer
  // **NOTE** one word is required for next spike tick word
  m_SpikeBlockSizeWords = BitField::GetWordSize(numNeurons) + 1;

  LOG_PRINT(LOG_LEVEL_INFO, "\tNext spike tick:%u, next spike block address:%08x, spike block words:%u",
            m_NextSpikeTick, m_NextSpikeBlockAddress, m_SpikeBlockSizeWords);

  unsigned int numBytes = m_SpikeBlockSizeWords * sizeof(uint32_t);
  m_DMABuffer = (uint32_t*)spin1_malloc(numBytes);
  if(m_DMABuffer == NULL)
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate %u byte DMA buffer", numBytes);
    return false;
  }

  // If the next spike occurs in the 1st timestep
  if(m_NextSpikeTick == 0)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Synchronously copying first spike block into DMA buffer");

    // Synchronously copy next block into DMA buffer
    spin1_memcpy(m_DMABuffer, m_NextSpikeBlockAddress, numBytes);

    // Advance next spike block address
    m_NextSpikeBlockAddress += m_SpikeBlockSizeWords;

    // Set state to reflect that there is data already in the buffer
    m_State = StateSpikeBlockInBuffer;

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    BitField::PrintBits(IO_BUF, &m_DMABuffer[1], m_SpikeBlockSizeWords - 1);
    io_printf(IO_BUF, "\n");
#endif
  }

  return true;
}
//-----------------------------------------------------------------------------
bool ArraySource::DMATransferDone(uint tag)
{
  // If DMA transfer is tagged correctly
  if(tag == DMATagSpikeDataRead)
  {
    // Check state
    if(m_State != StateDMAInProgress)
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "ArraySource::DMATransferDone received in state %u",
        m_State);
    }

    // Set state to reflect that there is now data in the buffer
    LOG_PRINT(LOG_LEVEL_TRACE, "DMA transfer complete");
    m_State = StateSpikeBlockInBuffer;

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    BitField::PrintBits(IO_BUF, &m_DMABuffer[1], m_SpikeBlockSizeWords - 1);
    io_printf(IO_BUF, "\n");
#endif
    return true;
  }
  else
  {
    return false;
  }
}
} // namespace Common