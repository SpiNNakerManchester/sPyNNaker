from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_with_payload_data_packet import EIEIOWithPayloadDataPacket


class EIEIO32BitWithPayloadPayloadPrefixDataPacket(EIEIOWithPayloadDataPacket):

    def __init__(self, payload_prefix, data=None):
        if data is None:
            data = bytearray()

        EIEIOWithPayloadDataPacket.__init__(
            self, EIEIOTypeParam.KEY_PAYLOAD_32_BIT,
            payload_base=payload_prefix, data=data)
