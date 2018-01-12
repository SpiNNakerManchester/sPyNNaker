#pragma once
#include <cstdint>
#include "rig_cpp_common/config.h"
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/spinnaker_cpp.h"


namespace ConnectionBuilder
{




#define REGION_START_INDEX 2

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
enum Region
{
  RegionSystem,
  RegionKeyLookup,
  RegionSynapticMatrix,
  RegionPlasticity,
  RegionOutputBuffer,
  RegionDelayBuffer,
  RegionBackPropagationInput,
  RegionConnectionBuilder,
  RegionProfiler,
  RegionStatistics,
};

// Indices of application words    
enum AppWord
{
  AppWordWeightFixedPoint,
  AppWordNumPostNeurons,
  AppWordFlushMask,
  AppWordMax,
};

//! human readable definitions of each region in SDRAM
// I think these should be in a higher level so c_main/conn_bldr can
// read them (change once, affect many)
    // names=[('SYSTEM', 0),
    //        ('NEURON_PARAMS', 1),
    //        ('SYNAPSE_PARAMS', 2),
    //        ('POPULATION_TABLE', 3),
    //        ('SYNAPTIC_MATRIX', 4),
    //        ('SYNAPSE_DYNAMICS', 5),
    //        ('RECORDING', 6),
    //        ('PROVENANCE_DATA', 7),
    //        ('PROFILING', 8),
    //        ('CONNECTOR_BUILDER', 9)])

typedef enum regions_e{
    SYSTEM_REGION,           //0
    NEURON_PARAMS_REGION,    //1
    SYNAPSE_PARAMS_REGION,   //2
    POPULATION_TABLE_REGION, //3
    SYNAPTIC_MATRIX_REGION,  //4
    SYNAPSE_DYNAMICS_REGION, //5
    RECORDING_REGION,        //6
    PROVENANCE_DATA_REGION,  //7
    PROFILING_REGION,
    CONNECTOR_BUILDER_REGION //9
} regions_e;

// FROM MAIN TOOLCHAIN front_end_common_lib/data_specification.c
uint32_t *data_specification_get_region(uint32_t region,
                                                uint32_t *data_address) {
    return (uint32_t *) (data_address[REGION_START_INDEX + region]);
}
uint32_t *data_specification_get_data_address(){

    // Get pointer to 1st virtual processor info struct in SRAM
//    LOG_PRINT(LOG_LEVEL_INFO, "SV_VCPU value = 0x%08x", SV_VCPU);
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;

    // Get the address this core's DTCM data starts at from the user data member
    // of the structure associated with this virtual processor
    LOG_PRINT(LOG_LEVEL_INFO, "Chip %u, Core %u", spin1_get_chip_id(),
              spin1_get_core_id());

    uint32_t *address =
        (uint32_t *) sark_virtual_processor_info[spin1_get_core_id()].user0;

    LOG_PRINT(LOG_LEVEL_INFO, "SDRAM data begins at address: %08x", address);
//    LOG_PRINT(LOG_LEVEL_INFO, "REGIONS begin at: %08x", address[REGION_START_INDEX]);
    uint32_t prev_addr = address[REGION_START_INDEX];
//    for(uint32_t i = 0; i < 8; i++){
//      LOG_PRINT(LOG_LEVEL_INFO, "REGION [%u] starts at: 0x%08x, size[%d]: %u", i, \
//                address[REGION_START_INDEX + i], i ,
//                address[REGION_START_INDEX + i + 1] - address[REGION_START_INDEX + i] );
//
//
//    }
    return address;
}



// end FROM MAIN TOOLCHAIN


} // ConnectionBuilder