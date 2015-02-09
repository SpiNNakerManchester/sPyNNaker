from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_without_payload_data_packet import EIEIOWithoutPayloadDataPacket


class EIEIO32BitPayloadPrefixUpperKeyPrefixDataPacket(
        EIEIOWithoutPayloadDataPacket):

    def __init__(self, key_prefix, payload_prefix, data=None):
        if data is None:
            data = bytearray()

        EIEIOWithoutPayloadDataPacket.__init__(
            self, EIEIOTypeParam.KEY_32_BIT, payload_base=payload_prefix,
            prefix_param=key_prefix,
            prefix_type=EIEIOPrefixType.UPPER_HALF_WORD, data=data)
