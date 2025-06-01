import ctypes

from .library import silkitapi
from .utilities import py2ct, auto_context

class SilKitSubscriber(object):
    def __init__(
        self,
        participant,
        name:str,
        topic:str,
        *,
        media_type:str = "application/vnd.vector.silkit.data; protocolVersion=1",
        callback = None,
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

        self.instance = silkitapi.SilKit_DataSubscriber_p()

        if callback is not None:
            if isinstance(callback, silkitapi.SilKit_DataMessageHandler_t):
                self.on_msg_recv = callback
            else:
                raise ValueError(f"Parameter callback must be an instance of {silkitapi.SilKit_DataMessageHandler_t.__name__}")
        else:
            self.on_msg_recv = self._on_data_message

        silkitapi.SilKit_DataSubscriber_Create(
            ctypes.byref(self.instance),
            self.participant.instance,
            self.name.encode(),
            ctypes.byref(self.data_spec),
            py2ct(self),
            self.on_msg_recv
        )

    @silkitapi.SilKit_DataMessageHandler_t
    @staticmethod
    @auto_context
    def _on_data_message(self, subscriber, event):
        payload = event.contents.data.to_sequence()
        print(f"[{self.name}] Received data: {payload}")
