from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_without_payload_data_packet import EIEIOWithoutPayloadDataPacket


class EIEIO16BitPayloadPrefixDataPacket(EIEIOWithoutPayloadDataPacket):

    def __init__(self, payload_prefix, data=None):
        if data is None:
            data = bytearray()

        EIEIOWithoutPayloadDataPacket.__init__(
            self, EIEIOTypeParam.KEY_16_BIT, payload_base=payload_prefix,
            data=data)
