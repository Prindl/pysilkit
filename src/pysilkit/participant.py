import ctypes
import enum

from typing import Union

from .library import silkitapi
from .can_controller import SilKitCanController
from .publisher import SilKitPublisher
from .subscriber import SilKitSubscriber

class CommunicationSystem(enum.IntEnum):
    CAN = 0
    ETHERNET = 1
    FLEXRAY = 2
    LIN = 3
    PUBLISHER = 4
    SUBSCRIBER = 5

class SilKitParticipant(object):
    __counter__ = 1
    __names__ = set()

    def __init__(
        self,
        name = None,
        port = 8500
    ):
        listen_uri = f"silkit://localhost:{port}"
        if name is None:
            self.name = f"Participant_{self.__counter__}"
            self.__counter__ += 1
        else:
            self.name = name
        if self.name in self.__names__:
            raise ValueError(f"{self.name} already exists")
        else:
            self.__names__.add(self.name)
        self.communication_controllers = {key: {} for key in CommunicationSystem}
        config = f"""
---
Description: Configuration of {self.name}
SchemaVersion: 1
ParticipantName: {self.name}
Logging:
  Sinks:
  - Type: File
    Level: Trace
    LogName: Log_
  FlushLevel: Trace
  LogFromRemotes: false
HealthCheck:
  SoftResponseTimeout: 500
  HardResponseTimeout: 5000
Middleware:
  RegistryUri: {listen_uri}
  ConnectAttempts: 9
  TcpNoDelay: true
  TcpQuickAck: true
  EnableDomainSockets: false
  TcpSendBufferSize: 3456
  TcpReceiveBufferSize: 3456
  RegistryAsFallbackProxy: false
  ConnectTimeoutSeconds: 1.234
"""
        self.instance_config =  silkitapi.SilKit_ParticipantConfiguration_p()
        silkitapi.SilKit_ParticipantConfiguration_FromString(
            ctypes.byref(self.instance_config),
            config.encode()
        )
        self.instance = silkitapi.SilKit_Participant_p()
        silkitapi.SilKit_Participant_Create(
            ctypes.byref(self.instance),
            self.instance_config,
            self.name.encode(),
            listen_uri.encode(),
        )
        self.__logger__ = silkitapi.SilKit_Logger_p()
        silkitapi.SilKit_Participant_GetLogger(
            ctypes.byref(self.__logger__),
            self.instance
        )

    def __del__(self):
        silkitapi.SilKit_Participant_Destroy(self.instance)
        silkitapi.SilKit_ParticipantConfiguration_Destroy(self.instance_config)

    def _log_(self, level:silkitapi.SilKitLoggingLevel, text:str):
        silkitapi.SilKit_Logger_Log(
            self.__logger__,
            level,
            text.encode()
        )

    def trace(self, text:str):
        self._log_(silkitapi.SilKitLoggingLevel.TRACE, text)

    def debug(self, text:str):
        self._log_(silkitapi.SilKitLoggingLevel.DEBUG, text)

    def info(self, text:str):
        self._log_(silkitapi.SilKitLoggingLevel.INFO, text)

    def warn(self, text:str):
        self._log_(silkitapi.SilKitLoggingLevel.WARN, text)

    def error(self, text:str):
        self._log_(silkitapi.SilKitLoggingLevel.ERROR, text)

    def critical(self, text:str):
        self._log_(silkitapi.SilKitLoggingLevel.CRITICAL, text)

    def _add_controller_(self, controller_type: CommunicationSystem, name, *args, **kwargs):
        controllers = self.communication_controllers[controller_type]
        if controller_type == CommunicationSystem.CAN:
            cls = SilKitCanController
        elif controller_type == CommunicationSystem.PUBLISHER:
            cls = SilKitPublisher
        elif controller_type == CommunicationSystem.SUBSCRIBER:
            cls = SilKitSubscriber
        else:
            raise NotImplementedError("")
        controllers[name] = cls(self, name, *args, **kwargs)

    def _get_controller_(self, controller_type: CommunicationSystem, i: Union[int, str]):
        controllers = self.communication_controllers[controller_type]
        if isinstance(i, int):
            try:
                key = list(controllers.keys())[i]
            except IndexError:
                raise ValueError(f"Controller '{controller_type.name}' {i} does not exist!")
        else:
            key = i
        try:
            return controllers[key]
        except KeyError:
            raise ValueError(f"Controller '{controller_type.name}' {key} does not exist!")

    def add_can_controller(self, name, network="VIRTUAL"):
        self._add_controller_(CommunicationSystem.CAN, name, network)

    def can(self, i: Union[int, str]):
        return self._get_controller_(CommunicationSystem.CAN, i)

    def add_publisher(
        self,
        name:str,
        topic:str,
        *,
        media_type:str = "application/vnd.vector.silkit.data; protocolVersion=1",
        history:bool = True,
        **labels
    ):
        self._add_controller_(
            CommunicationSystem.PUBLISHER, name,
            topic, media_type=media_type, history=history, **labels
        )

    def publisher(self, i: Union[int, str]):
        return self._get_controller_(CommunicationSystem.PUBLISHER, i)

    def add_subscriber(
        self,
        name:str,
        topic:str,
        *,
        media_type:str = "application/vnd.vector.silkit.data; protocolVersion=1",
        callback = None,
        history:bool = True,
        **labels
    ):
        self._add_controller_(
            CommunicationSystem.SUBSCRIBER, name,
            topic, media_type=media_type, callback=callback, history=history, **labels
        )

    def subscriber(self, i: Union[int, str]):
        return self._get_controller_(CommunicationSystem.SUBSCRIBER, i)

