/*
 * spin1-api-configuration.c
 *
 *
 *  SUMMARY
 *    Spin1-API dependent configuration routines
 *
 *  AUTHOR
 *    James Knight (knightk@man.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) James Knight and The University of Manchester, 2014.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *
 *
 *  CREATION DATE
 *    17 January, 2014
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 17 January 2014
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "common-impl.h"

// Globals
uint simulation_rtr_entry = 0;

address_t system_load_sram()
{
  // Get pointer to 1st virtual processor info struct in SRAM
  vcpu_t *sark_virtual_processor_info = (vcpu_t*)SV_VCPU;

  log_info("%08x", &sark_virtual_processor_info[spin1_get_core_id()].user0);

  // Get the address this core's DTCM data starts at from the user data member of the structure associated with this virtual processor
  address_t address = (address_t)sark_virtual_processor_info[spin1_get_core_id()].user0;

  log_info("SDRAM data begins at address:%08x", address);

  return address;
}

bool system_runs_to_completion()
{
  spin1_start(SYNC_WAIT);
  if (leadAp) {
//#ifndef DEBUG
      rtr_free_id(sark_app_id(), 1);
//#endif // n DEBUG
  }
  return (true);
}

bool system_data_extracted    () {                return (true); }
