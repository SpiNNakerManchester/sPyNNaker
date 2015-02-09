from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_with_payload_data_packet import EIEIOWithPayloadDataPacket


class EIEIO16BitWithPayloadPayloadPrefixLowerKeyPrefixDataPacket(
        EIEIOWithPayloadDataPacket):

    def __init__(self, key_prefix, payload_prefix, data=None):
        if data is None:
            data = bytearray()

        EIEIOWithPayloadDataPacket.__init__(
            self, EIEIOTypeParam.KEY_PAYLOAD_16_BIT, prefix_param=key_prefix,
            prefix_type=EIEIOPrefixType.LOWER_HALF_WORD,
            payload_base=payload_prefix, data=data)
