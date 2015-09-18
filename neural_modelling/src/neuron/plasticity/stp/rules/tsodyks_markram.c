#include "tsodyks_markram_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
int16_t tau_syn_lut[TAU_SYN_LUT_SIZE];
int16_t tau_rec_lut[TAU_REC_LUT_SIZE];
int16_t tau_fac_lut[TAU_FAC_LUT_SIZE];

stp_region_data_t stp_region_data;

//---------------------------------------
// Functions
//---------------------------------------
address_t stp_initialise(address_t address)
{
  log_info("stp_initialise: starting");
  log_info("\tTsodyks Markram rule");

  // Read Tsodyks Markram parameters
  int32_t *plasticity_word = (int32_t*) address;
  stp_region_data.asymptotic_prob_release = *plasticity_word++;
  stp_region_data.tau_rec_over_psc_rec = *plasticity_word++;
  stp_region_data.tau_psc_over_psc_rec = *plasticity_word++;

  log_info("\tasymptotic_prob_release:%d, tau_rec_over_psc_rec:%d, tau_psc_over_psc_rec:%d",
           stp_region_data.asymptotic_prob_release, stp_region_data.tau_rec_over_psc_rec,
           stp_region_data.tau_psc_over_psc_rec);
  
  // Copy LUTs from following memory
  address_t lut_address = maths_copy_int16_lut((address_t)plasticity_word, TAU_SYN_LUT_SIZE,
                                               &tau_syn_lut[0]);
  lut_address = maths_copy_int16_lut(lut_address, TAU_REC_LUT_SIZE,
                                     &tau_rec_lut[0]);
  lut_address = maths_copy_int16_lut(lut_address, TAU_FAC_LUT_SIZE,
                                     &tau_fac_lut[0]);

  log_info("stp_initialise: completed successfully");

  return lut_address;
}
