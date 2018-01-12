#include "connector_generator.h"

// Standard includes
#include <algorithm>

// Rig CPP common includes
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/random/mars_kiss64.h"
#include "rig_cpp_common/maths/hypergeometric.h"
#include "rig_cpp_common/maths/binomial.h"

using namespace Common::Maths;
using namespace ConnectionBuilder::KernelMaths;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::AllToAll
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::AllToAll::AllToAll(uint32_t *&region)
{
  m_AllowSelfConnections = *region++;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tAll-to-all connector: Allow self connections: %u",
            m_AllowSelfConnections);
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::AllToAll::Generate(
                                     uint32_t pre_start, uint32_t pre_count,
                                     uint32_t pre_idx,
                                     uint32_t post_start, uint32_t post_count,
                                     uint32_t max_indices,
                                     MarsKiss64 &rng, uint16_t (&indices)[512])
{
  
  unsigned int num_conns = 0;
//  uint32_t pre_abs = pre_start + pre_idx;
  for(uint32_t post = 0; post < post_count; post++){

      if(!m_AllowSelfConnections && (post_start + post) == pre_idx)
        continue;
      indices[post] = post;
      num_conns++;
  }
  return num_conns;
}




//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::Mapping
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::Mapping::Mapping(uint32_t *&region){

    m_width   = (uint16_t)( (*region) >> 16 );
    m_height  = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_channel     = (uint8_t)( (*region) & 0xFF );
    m_eventBits   = (uint8_t)( ((*region) >> 8) & 0xFF );
    m_channelBits = (uint8_t)( ((*region) >> 16) & 0xFF );
    m_heightBits     = (uint8_t)( ((*region) >> 24) & 0xFF );

    region++;

    LOG_PRINT(LOG_LEVEL_INFO, "\t\tMapping Connector:");
    io_printf(IO_BUF,
     "\t\t\t\tShape %d, %d; channel %d, rowBits %d, channelBits %d, eventBits %u\n",
     m_width, m_height, m_channel, m_heightBits, m_channelBits, m_eventBits);

}


unsigned int ConnectionBuilder::ConnectorGenerator::Mapping::Generate(
                                     uint32_t pre_start, uint32_t pre_count,
                                     uint32_t pre_idx,
                                     uint32_t post_start, uint32_t post_count,
                                     uint32_t max_indices,
                                     MarsKiss64 &rng, uint16_t (&indices)[512]){
//  LOG_PRINT(LOG_LEVEL_INFO, "-------------------In Mapping Connector Generator");

  uint16_t chan = (pre_idx >> m_eventBits) & ((1 << m_channelBits) - 1);

  if (chan != m_channel || pre_idx == 1 || pre_idx == 0){
  // TODO: not cool, this should be passed in from python
//    io_printf(IO_BUF, "not the right channel!!!\n");
//    io_printf(IO_BUF, "Channel %u\tEvent %u\n", chan, event);
    return 0;
  }
  uint8_t n_conns=0;

  // X
  uint16_t pre_c = pre_idx >> (m_heightBits + m_channelBits + m_eventBits);
  // Y
  uint16_t pre_r = (pre_idx >> (m_channelBits + m_eventBits)) & \
                   ((1 << m_heightBits) - 1);

  uint16_t post_c;
  uint16_t post_r = uidiv(post_start, m_width, post_c);
  uint16_t post_end_r = uidiv((post_start+post_count), m_width, post_c);

//  io_printf(IO_BUF, "pre %d < %d post s OR pre %d > %d post e \n",
//                       pre_r, post_r, pre_r, post_end_r);
  if(pre_r < post_r || post_end_r < pre_r){
    return 0;
  }


  for(uint16_t post_idx = post_start; post_idx < post_start + post_count;
      post_idx++){
    //post row and col from index
    post_r = uidiv(post_idx, m_width, post_c);
//    io_printf(IO_BUF, "(%d, %d) == (%d, %d)?\n",
//              pre_r, pre_c, post_r, post_c);
    if(pre_c == post_c && pre_r == post_r ){
//      io_printf(IO_BUF, "pre %d == (%d, %d) == post %d\n",
//                pre_idx, pre_r, pre_c, post_idx);
      indices[n_conns] = post_idx - post_start;
      return 1;
    }
  }

  return 0;

}


//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::Kernel
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::Kernel::Kernel(uint32_t *&region){

    m_commonWidth   = (uint16_t)( (*region) >> 16 );
    m_commonHeight  = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_preWidth   = (uint16_t)( (*region) >> 16 );
    m_preHeight  = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_postWidth  = (uint16_t)( (*region) >> 16 );
    m_postHeight = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_startPreWidth  = (uint16_t)( (*region) >> 16 );
    m_startPreHeight = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_startPostWidth  = (uint16_t)( (*region) >> 16 );
    m_startPostHeight = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_stepPreWidth  = (uint16_t)( (*region) >> 16 );
    m_stepPreHeight = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_stepPostWidth  = (uint16_t)( (*region) >> 16 );
    m_stepPostHeight = (uint16_t)( (*region) & 0xFFFF );
    region++;

    m_kernelWidth  = (uint16_t)( (*region) >> 16 );
    m_kernelHeight = (uint16_t)( (*region) & 0xFFFF );
    region++;

    LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tKernel-based Connector:");
    io_printf(IO_BUF, "\t\t\t\tpre(%d, %d) => post(%d, %d)\n",
              m_preWidth, m_preHeight, m_postWidth, m_postHeight);
    io_printf(IO_BUF, "\t\t\t\tkernel(%d, %d), start(%d, %d), step(%d, %d)\n",
              m_kernelWidth, m_kernelHeight,
              m_startPostWidth, m_startPostHeight,
              m_stepPostWidth, m_stepPostHeight);
}





unsigned int ConnectionBuilder::ConnectorGenerator::Kernel::Generate(
                                     uint32_t pre_start, uint32_t pre_count,
                                     uint32_t pre_idx,
                                     uint32_t post_start, uint32_t post_count,
                                     uint32_t max_indices,
                                     MarsKiss64 &rng, uint16_t (&indices)[512]){
//  LOG_PRINT(LOG_LEVEL_INFO, "-------------------In Kernel Connector Generator");
  uint32_t index_count = 0;
  uint16_t pre_c;// = pre_idx%m_preWidth;
  uint16_t pre_r = uidiv(pre_idx, m_preWidth, pre_c);
//  LOG_PRINT(LOG_LEVEL_INFO, "Computed pre %d == (%d, %d)",
//            pre_idx, pre_r, pre_c);


  for(uint16_t post_idx = post_start; post_idx < post_start + post_count;
      post_idx++){
    //post row and col from index
    uint16_t post_c;
    uint16_t post_r = uidiv(post_idx, m_postWidth, post_c);

    //post in common coordinate system
    int16_t pac_r = m_startPostHeight + post_r*m_stepPostHeight;
    int16_t pac_c = m_startPostWidth  + post_c*m_stepPostWidth;
    if( pac_r < 0 || pac_r >= m_commonHeight ||
        pac_c < 0 || pac_c >= m_commonWidth){
      continue;
    }
    int16_t pap_r, pap_c;
    //convert from common to pre coordinates
    pre_in_post_world(pac_r, pac_c, m_startPreHeight, m_startPreWidth,
                      m_stepPreHeight, m_stepPreWidth, pap_r, pap_c);

    //start of pre coordinates range (in pre coord system)
    int16_t r_start = std::max<int16_t>(pap_r - (m_kernelHeight >> 1), 0);
    int16_t c_start = std::max<int16_t>(pap_c - (m_kernelWidth  >> 1), 0);

    //end of pre coordinates range (in pre coord system)
    int16_t r_end = std::min<int16_t>(pap_r + (m_kernelHeight >> 1) + 1, m_preHeight);
    int16_t c_end = std::min<int16_t>(pap_c + (m_kernelWidth  >> 1) + 1, m_preWidth);



//    LOG_PRINT(LOG_LEVEL_INFO, "Post i%u (%u, %u): from(%u, %u) to (%u, %u)",
//              post_idx, pap_r, pap_c, r_start, c_start, r_end, c_end);

    if( (r_start <= pre_r) && (pre_r < r_end) &&
        (c_start <= pre_c) && (pre_c < c_end) ){
//        LOG_PRINT(LOG_LEVEL_INFO, "pre (%u, %u) => post(%u, %u)",
//                  pre_r, pre_c, r, c);
      bool continue_outer = false;
      for(uint16_t s = 0; s < index_count; s++){
        if(indices[s] == post_idx){
          continue_outer = true;
          break;
        }
      }
      if(continue_outer){ continue; }
//      LOG_PRINT(LOG_LEVEL_INFO, "\tpre (%u, %u) => post(%u, %u) accepted",
//                pre_r, pre_c, pap_r, pap_c);
//          LOG_PRINT(LOG_LEVEL_INFO, "accepted post %d", post_idx);
      indices[index_count] = post_idx - post_start;
      index_count++;

    }
  }

  return index_count;
}


//-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::OneToOne
//-----------------------------------------------------------------------------
ConnectionBuilder::ConnectorGenerator::OneToOne::OneToOne(uint32_t *&)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tOne-to-one connector");
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::ConnectorGenerator::OneToOne::Generate(
                                     uint32_t pre_start, uint32_t pre_count,
                                     uint32_t pre_idx,
                                     uint32_t post_start, uint32_t post_count,
                                     uint32_t max_indices,
                                     MarsKiss64 &rng, uint16_t (&indices)[512])
{
//  pre_idx += pre_start; //make pre index into global scale
  const bool in_range = ((pre_idx >= post_start) && (pre_idx < post_start+post_count));

  if(in_range){
    indices[0] = pre_idx - post_start;
    return 1;
  } else {
    return 0;
  }
}

// //-----------------------------------------------------------------------------
// // ConnectionBuilder::ConnectorGenerator::FixedProbability
// //-----------------------------------------------------------------------------
 ConnectionBuilder::ConnectorGenerator::FixedProbability::FixedProbability(uint32_t *&region)
 {
   m_AllowSelfConnections = *region++;
   m_Probability = *region++;

   LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed-probability connector: probability:%u",
     m_Probability);
 }
 //-----------------------------------------------------------------------------
 unsigned int ConnectionBuilder::ConnectorGenerator::FixedProbability::Generate(
                                      uint32_t pre_start, uint32_t pre_count,
                                      uint32_t pre_idx,
                                      uint32_t post_start, uint32_t post_count,
                                      uint32_t max_indices,
                                      MarsKiss64 &rng, uint16_t (&indices)[512])
 {

   // Write indices
   unsigned int post;
   unsigned int num_conns = 0;
   uint32_t dice_roll = 0;
   for(post = 0; post < post_count; post++)
   {
     // If draw if less than probability, add index to row
     dice_roll = rng.GetNext();

//     LOG_PRINT(LOG_LEVEL_INFO, "dice = %u < %u", dice_roll, m_Probability);
//     if(rng.GetNext() < m_Probability)
     if(dice_roll <= m_Probability)
     {

       if (!m_AllowSelfConnections && (post+post_start) == pre_idx ){
         continue;
       }
       indices[num_conns++] = post;

     }

     if(num_conns == max_indices){
        return num_conns;
     }
   }

   return num_conns;
 }

// //-----------------------------------------------------------------------------
// // ConnectionBuilder::ConnectorGenerator::FixedTotalNumber
// //-----------------------------------------------------------------------------
// ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::FixedTotalNumber(uint32_t *&region)
// {
//   m_AllowSelfConnections = *region++;
//   m_WithReplacement = *region++;
//   m_ConnectionsInSubmatrix = *region++;
//   m_SubmatrixSize = *region++;

//   LOG_PRINT(LOG_LEVEL_INFO, "\t\tFixed total number connector: connections in submatrix: %u, "
//             "with replacement: %u", m_ConnectionsInSubmatrix, m_WithReplacement);
// }
// //-----------------------------------------------------------------------------
// unsigned int ConnectionBuilder::ConnectorGenerator::FixedTotalNumber::Generate(
//                                      uint32_t pre_start, uint32_t pre_count,
//                                      uint32_t post_start, uint32_t post_count,
//                                      MarsKiss64 &rng, uint32_t (&indices)[512])
// {
//   // Determine how many of the submatrix connections are within this row
//   // If there are no connections left to allocate to a row,
//   // then there are no connections in this row
//   unsigned int numInRow;
//   if (m_ConnectionsInSubmatrix == 0)
//   {
//     numInRow = 0;
//   }
//   // If we're on the last row of the submatrix, then all of the remaining
//   // submatrix connections get allocated to this row
//   else if (numPostNeurons == m_SubmatrixSize)
//   {
//     numInRow = m_ConnectionsInSubmatrix;
//   }
//   // Otherwise, sample from the distribution over the number of the submatrix
//   // connections that will end up within this row. The distribution depends
//   // on whether the connections are made with or without replacement
//   else
//   {
//     // Sample from a binomial distribution to determine how many of
//     // the submatrix connections are within this row
//     if (m_WithReplacement)
//     {
//       // Each of the connections has a (row size)/(submatrix size)
//       // probability of ending up in this row
//       numInRow = Binomial(m_ConnectionsInSubmatrix,
//                           numPostNeurons,
//                           m_SubmatrixSize, rng);
//     }
//     // Sample from a hypergeometric distribution to determine how many of
//     // the submatrix connections are within this row
//     else
//     {
//       // In the whole submatrix, there are some number of connections,
//       // some number of non-connections, and our row is a random sample
//       // of (row size) of them
//       numInRow = Hypergeom(m_ConnectionsInSubmatrix,
//                            m_SubmatrixSize - m_ConnectionsInSubmatrix,
//                            numPostNeurons, rng);
//     }
//   }

//   // Clamp numInRow down to buffer size
//   numInRow = std::min<unsigned int>(numInRow, 512);

//   // Sample from the possible connections in this row numInRow times
//   if (m_WithReplacement)
//   {
//     // Sample them with replacement
//     for(unsigned int i=0; i<numInRow; i++)
//     {
//       const unsigned int u01 = (rng.GetNext() & 0x00007fff);
//       const unsigned int j = (u01 * numPostNeurons) >> 15;
//       indices[i] = j;
//     }
//   }
//   else
//   {
//     // Sample them without replacement using reservoir sampling
//     for(unsigned int  i=0; i<numInRow; i++)
//     {
//       indices[i] = i;
//     }
//     for(unsigned int i=numInRow; i<numPostNeurons; i++)
//     {
//       // j = rand(0, i) (inclusive)
//       const unsigned int u01 = (rng.GetNext() & 0x00007fff);
//       const unsigned int j = (u01 * (i+1)) >> 15;
//       if (j < numInRow)
//       {
//         indices[j] = i;
//       }
//     }
//   }

//   m_ConnectionsInSubmatrix -= numInRow;
//   m_SubmatrixSize -= numPostNeurons;

//   return numInRow;
// }
