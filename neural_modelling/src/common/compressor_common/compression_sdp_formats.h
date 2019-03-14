#include "common-typedefs.h"

#ifndef __COMPRESSION_SDP_FORMATS_H__


//! \brief the elements in the sdp packet (control for setting off a minimise
//! attempt)
typedef struct start_stream_sdp_packet_t{
    address_t address_for_compressed;
    address_t fake_heap_data;
    uint32_t n_sdp_packets_till_delivered;
    uint32_t total_n_tables;
    uint32_t n_tables_in_packet;
    address_t tables[];
} start_stream_sdp_packet_t;

//! \brief the elements in the sdp packet when extension control for a minimise
//! attempt. Only used when x routing tables wont fit in first packet
typedef struct extra_stream_sdp_packet_t{
    uint32_t n_tables_in_packet;
    address_t tables[];
} extra_stream_sdp_packet_t;

//! \brief the elements in the sdp packet when response to compression attempt.
typedef struct response_sdp_packet_t{
    uint32_t command_code;
    uint32_t response_code;
} response_sdp_packet_t;

//! \brief the acceptable finish states
typedef enum finish_states{
    SUCCESSFUL_COMPRESSION = 30, FAILED_MALLOC = 31, FAILED_TO_COMPRESS = 32,
    RAN_OUT_OF_TIME = 33, FORCED_BY_COMPRESSOR_CONTROL = 34, SHUT_DOWN = 35
} finish_states;

//! location where the blasted command code is
typedef enum points_in_sdp_message_top_level{
    COMMAND_CODE = 0, START_OF_SPECIFIC_MESSAGE_DATA = 1
} points_in_sdp_message_top_level;

//! \brief the command codes in human readable form
typedef enum command_codes_for_sdp_packet{
    START_DATA_STREAM = 20,
    EXTRA_DATA_STREAM = 21,
    COMPRESSION_RESPONSE = 22,
    STOP_COMPRESSION_ATTEMPT = 23
} command_codes_for_sdp_packet;

#define COMMAND_CODE_SIZE_IN_BYTES 4

#define __COMPRESSION_SDP_FORMATS_H__
#endif  // __COMPRESSION_SDP_FORMATS_H__
