import ctypes

from .library import silkitapi

class SilKitPublisher(object):
    def __init__(
        self,
        participant,
        name:str,
        topic:str,
        *,
        media_type:str = "application/vnd.vector.silkit.data; protocolVersion=1",
        history:bool = True,
        **labels
    ):
        self.participant = participant
        self.name = name
        self.topic = topic
        self.media_type = media_type
        self.data_spec = silkitapi.SilKit_DataSpec()
        self.data_spec.structHeader = silkitapi.SilKit_StructHeader(
            version=silkitapi.SilKit_STRUCT_VERSION.DataSpec
        )
        self.data_spec.topic = self.topic.encode()
        self.data_spec.mediaType = self.media_type.encode()
        if labels is not None:
            self.data_spec.labelList = silkitapi.SilKit_LabelList.from_dict(**labels)

        self.instance = silkitapi.SilKit_DataPublisher_p()
        silkitapi.SilKit_DataPublisher_Create(
            ctypes.byref(self.instance),
            self.participant.instance,
            self.name.encode(),
            ctypes.byref(self.data_spec),
            int(history)
        )

    def publish(self, data):
        byte_vector = silkitapi.SilKit_ByteVector.from_sequence(data)
        silkitapi.SilKit_DataPublisher_Publish(self.instance, ctypes.byref(byte_vector))
