#ifndef __COMPRESSION_SDP_FORMATS_H__

//! \brief the elements in the sdp packet (control for setting off a minimise
//! attempt)
typedef enum data_elements_in_start_stream_sdp_packet{
    ADDRESS_FOR_COMPRESSED = 1, FAKE_HEAP_DATA = 2,
    N_SDP_PACKETS_TILL_DELIVERED = 3, TOTAL_N_ADDRESSES = 4,
    N_ADDRESSES_IN_PACKET = 5, START_OF_ADDRESSES = 6
} data_elements_in_start_stream_sdp_packet;

//! \brief the element in the sdp packet when extension control for a minimise
//! attempt. Only used when x routing tables wont fit in first packet
typedef enum data_elements_in_extension_stream_sdp_packet{
    EXTRA_STREAM_N_ADDRESSES = 1, START_OF_ADDRESSES_EXTENSION = 2
} data_elements_in_extension_stream_sdp_packet;

//! \brief the elements in the sdp packet when responding to a compression
//! attempt
typedef enum data_elements_in_response_compression_sdp_packet{
    FINISHED_STATE = 1, LENGTH_OF_ACK_PACKET = 2
} data_elements_in_response_compression_sdp_packet;

//! \brief the acceptable finish states
typedef enum finish_states{
    SUCCESSFUL_COMPRESSION = 30, FAILED_MALLOC = 31, FAILED_TO_COMPRESS = 32,
    RAN_OUT_OF_TIME = 33, FORCED_BY_COMPRESSOR_CONTROL = 34
} finish_states;

//! location where the blasted command code is
#define COMMAND_CODE 0

//! \brief the command codes in human readable form
typedef enum command_codes_for_sdp_packet{
    START_OF_COMPRESSION_DATA_STREAM = 20,
    EXTRA_DATA_FOR_COMPRESSION_DATA_STREAM = 21,
    COMPRESSION_RESPONSE = 22,
    STOP_COMPRESSION_ATTEMPT = 23
} command_codes_for_sdp_packet;

#define __COMPRESSION_SDP_FORMATS_H__
#endif  // __COMPRESSION_SDP_FORMATS_H__
