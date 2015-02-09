from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_without_payload_data_packet import EIEIOWithoutPayloadDataPacket


class EIEIO32BitTimedPayloadPrefixDataPacket(EIEIOWithoutPayloadDataPacket):

    def __init__(self, timestamp, data=None):
        if data is None:
            data = bytearray()

        EIEIOWithoutPayloadDataPacket.__init__(
            self, EIEIOTypeParam.KEY_32_BIT, payload_base=timestamp,
            is_time=True, data=data)
