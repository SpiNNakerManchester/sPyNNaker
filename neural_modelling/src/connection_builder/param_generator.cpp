#include "param_generator.h"

// Standard includes
#include <algorithm>

// Rig CPP common includes
#include "rig_cpp_common/fixed_point_number.h"
#include "rig_cpp_common/arm_intrinsics.h"
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/maths/normal.h"
#include "rig_cpp_common/random/non_uniform.h"
#include "rig_cpp_common/random/mars_kiss64.h"


// Namespaces
using namespace Common::ARMIntrinsics;
using namespace Common::Maths;
using namespace Common::Random::NonUniform;
using namespace Common::FixedPointNumber;

using namespace ConnectionBuilder::KernelMaths;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerator::ConvKernel
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::ConvKernel::ConvKernel(uint32_t *&region){

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

    LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tKernel parameter: ");
//    LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\tpre(%d, %d) => post(%d, %d)",
//              m_preWidth, m_preHeight, m_postWidth, m_postHeight);
//    LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\tkernel(%d, %d), start(%d, %d), step(%d, %d)",
//              m_kernelWidth, m_kernelHeight,
//              m_startPostWidth, m_startPostHeight,
//              m_stepPostWidth, m_stepPostHeight);


    m_values = (int32_t *)region; //don't copy values, just address
    region += m_kernelHeight*m_kernelWidth;

//    LOG_PRINT(LOG_LEVEL_INFO, "\t\t\t\tValues:\n");
//    for(uint32_t r = 0; r < m_kernelHeight; r++){
//      io_printf(IO_BUF, "\t[ ");
//      for(uint32_t c = 0; c < m_kernelWidth; c++){
//        if( m_values[r*m_kernelWidth + c] < 0 ){
//          io_printf(IO_BUF, "-%4.6k\t", (-m_values[r*m_kernelWidth + c]));
//        }
//        else{
//          io_printf(IO_BUF, " %4.6k\t", m_values[r*m_kernelWidth + c]);
//        }
//      }
//      io_printf(IO_BUF, " ]\n");
//    }
//    io_printf(IO_BUF, "\n");
}

void ConnectionBuilder::ParamGenerator::ConvKernel::Generate(
                                             unsigned int num_params, unsigned int shift,
                                             uint32_t pre_idx,
                                             uint32_t post_start, uint16_t (indices)[512],
                                             MarsKiss64 &, int32_t (&output)[512]) const
{
  uint16_t pre_c = 0;
  uint16_t pre_r = uidiv(pre_idx, m_preWidth, pre_c);

  uint16_t hlf_kw = m_kernelWidth  >> 1;
  uint16_t hlf_kh = m_kernelHeight >> 1;
  int16_t k_r, k_c;
  for(uint16_t i = 0; i < num_params; i++){
    uint16_t post_r, post_c; //post raw
    uint16_t pac_r, pac_c;// post as common
    int16_t pap_r, pap_c;// post as pre
    post_r = uidiv(post_start + indices[i], m_postWidth, post_c);

    //move post coords into common coordinate system
    post_in_pre_world(post_r, post_c, m_startPostHeight, m_startPostWidth,
                      m_stepPostHeight, m_stepPostWidth, pac_r, pac_c);

    //move common to pre coords
    pre_in_post_world(pac_r, pac_c, m_startPreHeight, m_startPreHeight,
                      m_stepPreHeight, m_stepPreWidth, pap_r, pap_c);

    int16_t r_diff = (int16_t)pap_r - (int16_t)pre_r;
    int16_t c_diff = (int16_t)pap_c - (int16_t)pre_c;

    k_r = hlf_kh - r_diff;
    k_c = hlf_kw - c_diff;

//    LOG_PRINT(LOG_LEVEL_INFO,
//              "post(%u, %u)[%u] - pre(%u, %u)[%u] => D(%d, %d) => krn(%d, %d)",
//              pap_r, pap_c, post_r*m_postWidth + post_c,
//              pre_r, pre_c, pre_r*m_preWidth + pre_c,
//              r_diff, c_diff, k_r, k_c);

    if(0 <= k_r && k_r < m_kernelHeight &&
       0 <= k_c && k_c < m_kernelWidth){
//      LOG_PRINT(LOG_LEVEL_INFO, "val = %5.6k", m_values[k_r*m_kernelWidth + k_c]);
      output[i] = m_values[k_r*m_kernelWidth + k_c] >> (16-shift);
//      LOG_PRINT(LOG_LEVEL_INFO, "val = %5.6k", output[i]);
    }
    else {
      LOG_PRINT(LOG_LEVEL_ERROR, "Kernel coordinates off range (%d, %d)",
                k_r, k_c);
    }

  }

}


//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerator::Constant
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::Constant::Constant(uint32_t *&region)
{
  m_Value = *reinterpret_cast<int32_t*>(region++);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tConstant parameter: value:%d", m_Value);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Constant::Generate(
                                             unsigned int number, unsigned int shift,
                                             uint32_t pre_idx,
                                             uint32_t post_start, uint16_t (indices)[512],
                                             MarsKiss64 &, int32_t (&output)[512]) const
{
  // Copy constant into output
  for(uint32_t i = 0; i < number; i++)
  {
    output[i] = m_Value >> 16;
  }
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::Uniform
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::Uniform::Uniform(uint32_t *&region)
{
  m_Low = *reinterpret_cast<int32_t*>(region++);
  const int32_t high = *reinterpret_cast<int32_t*>(region++);
  m_Range = high - m_Low;

  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tUniform parameter: low:%d, high:%d, range:%d",
            m_Low, high, m_Range);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Uniform::Generate(
                                         unsigned int number, unsigned int shift,
                                         uint32_t pre_idx,
                                         uint32_t post_start, uint16_t (indices)[512],
                                         MarsKiss64 &rng, int32_t (&output)[512]) const
{
  uint32_t i = 0;
  while(i < number)
  {
    // Draw random number (0, UINT32_MAX) since 1 == UINT32_MAX and
    // I need U1616, I shift down half val for fraction value
    int32_t fraction = (int32_t)((rng.GetNext() >> 16) );

    // Multiply the resultant fraction by the range and shift down
    // shift var due to mixed fixed-point representation

    output[i] = (m_Low + (uint32_t)( __smull(fraction, m_Range) >> 16) ) >> (16-shift);
    i++;
  }
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::Normal
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::Normal::Normal(uint32_t *&region)
{
  m_Mu = *reinterpret_cast<int32_t*>(region++);
  m_Sigma = *reinterpret_cast<int32_t*>(region++);
  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tNormal parameter: mu:%d, sigma:%d",
            m_Mu, m_Sigma);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Normal::Generate(
                                         unsigned int number, unsigned int shift,
                                         uint32_t pre_idx,
                                         uint32_t post_start, uint16_t (indices)[512],
                                         MarsKiss64 &rng, int32_t (&output)[512]) const
{
  for(uint32_t i = 0; i < number; i++)
  {

    // **TODO** why is sign later being thrown away?

    // Draw random number (0, UINT32_MAX)
    uint32_t uniform = rng.GetNext();
    // Transform into standard uniform random variable
    // add location parameter and scale
    int32_t normal = m_Mu + MulS1615(NormalU032(uniform), m_Sigma);

    output[i] = normal >> (16 - shift);
  }
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::NormalClipped
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::NormalClipped::NormalClipped(uint32_t *&region)
{
  m_Mu = *reinterpret_cast<int32_t*>(region++);
  m_Sigma = *reinterpret_cast<int32_t*>(region++);

  //**YUCK** weight distributions may lie between negative bounds
  // BUT for unsigned synaptic matrices the signs will be flipped
  // so 'low' may infact be larger than 'high' leading to an infinite loop
  int32_t low = *reinterpret_cast<int32_t*>(region++);
  int32_t high = *reinterpret_cast<int32_t*>(region++);
  m_Low = std::min(low, high);
  m_High = std::max(low, high);

  LOG_PRINT(LOG_LEVEL_INFO,
            "\t\t\tNormal clipped parameter: mu:%d, sigma:%d, low:%d, high:%d",
            m_Mu, m_Sigma, m_Low, m_High);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::NormalClipped::Generate(
                                         unsigned int number, unsigned int shift,
                                         uint32_t pre_idx,
                                         uint32_t post_start, uint16_t (indices)[512],
                                         MarsKiss64 &rng, int32_t (&output)[512]) const
{
  for(uint32_t i = 0; i < number; i++)
  {

    int32_t normal;

    // **TODO** some kind of check to make sure we don't end up in inf. loop
    do
    {
      // Draw random number (0, UINT32_MAX)
      uint32_t uniform = rng.GetNext();
      // Transform into standard uniform random variable, add location parameter and scale
      normal = m_Mu + MulS1615(NormalU032(uniform), m_Sigma);
    } while (normal > m_High || normal < m_Low);

    output[i] = normal;
  }
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::NormalClippedToBoundary
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::NormalClippedToBoundary::NormalClippedToBoundary(uint32_t *&region)
{
  m_Mu = *reinterpret_cast<int32_t*>(region++);
  m_Sigma = *reinterpret_cast<int32_t*>(region++);
  m_Low = *reinterpret_cast<int32_t*>(region++);
  m_High = *reinterpret_cast<int32_t*>(region++);
  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tNormal clipped to boundary parameter:\
                             mu:%d, sigma:%d, low:%d, high:%d",
            m_Mu, m_Sigma, m_Low, m_High);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::NormalClippedToBoundary::Generate(
                                         unsigned int number, unsigned int shift,
                                         uint32_t pre_idx,
                                         uint32_t post_start, uint16_t (indices)[512],
                                         MarsKiss64 &rng, int32_t (&output)[512]) const
{
  for(uint32_t i = 0; i < number; i++)
  {

    // Draw random number (0, UINT32_MAX)
    uint32_t uniform = rng.GetNext();
    // Transform into standard uniform random variable, add location parameter and scale
    int32_t normal = m_Mu + MulS1615(NormalU032(uniform), m_Sigma);

    // Clip output to boundary
    if (normal < m_Low)
    {
      normal = m_Low;
    }
    if (normal > m_High)
    {
      normal = m_High;
    }
    output[i] = normal;
  }
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::Exponential
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::Exponential::Exponential(uint32_t *&region)
{
  m_Beta = *reinterpret_cast<int32_t*>(region++);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tExponential parameter: beta:%d",
            m_Beta);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Exponential::Generate(
                                         unsigned int number, unsigned int shift,
                                         uint32_t pre_idx,
                                         uint32_t post_start, uint16_t (indices)[512],
                                         MarsKiss64 &rng, int32_t (&output)[512]) const
{
  for(uint32_t i = 0; i < number; i++)
  {
    int32_t exp = MulS1615(m_Beta, ExponentialDistVariate(rng));
    output[i] = exp >> (16 - shift);
  }
}
