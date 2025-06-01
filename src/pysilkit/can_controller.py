import collections
import ctypes
from datetime import datetime, timezone
import time

from .library import silkitapi
from .utilities import py2ct, auto_context

from .time_slave import SilKitTimeSlave

GLOBAL_TIME = time.perf_counter()

class CanMessage(object):
    def __init__(
            self,
            id,
            *data,
            timestamp = 0.0,
            is_can_fd = False,
            is_can_xl = False,
            is_remote_frame = False,
            is_rx_fame = False,
            bitrate_switch = False,
            error_state_indicator = False,
            #XL Parameters
            sdt = 0,
            vcid = 0,
            af = 0
    ):
        self.id = id
        self.is_can_fd = is_can_fd
        self.is_can_xl = is_can_xl
        self.is_remote_frame = is_remote_frame
        self.is_rx_fame = is_rx_fame
        self.bitrate_switch = bitrate_switch
        self.error_state_indicator = error_state_indicator
        self.dlc = len(data)
        self.sdt = sdt # service data unit (CiA611-1: SDT=0x05 is Ethernet Frame)
        self.vcid = vcid # Virtual Can Network id
        self.af = af # acceptance field / Can ID for XL
        self.data = data
        self.timestamp = timestamp

    def __str__(self):
        tmp = datetime.fromtimestamp(self.timestamp, tz=timezone.utc).strftime("%d/%m/%Y %H:%M:%S.%f")
        # tmp = self.timestamp
        return f"{tmp} 0x{self.id:02X}: {self.data}"

    def to_silkit(self):
        flags = 0
        if self.is_remote_frame:
            flags |= silkitapi.SilKitCanFrameFlag.RTR
        if self.is_can_fd:
            flags |= silkitapi.SilKitCanFrameFlag.FDF
        if self.bitrate_switch:
            flags |= silkitapi.SilKitCanFrameFlag.BRS
        if self.error_state_indicator:
            flags |= silkitapi.SilKitCanFrameFlag.ESI
        if self.is_can_xl:
            flags |= silkitapi.SilKitCanFrameFlag.XLF
        # if self.todo:
        #     flags |= silkitapi.SilKitCanFrameFlag.SEC
        return silkitapi.SilKit_CanFrame(
            structHeader=silkitapi.SilKit_StructHeader(version=silkitapi.SilKit_STRUCT_VERSION.CanFrame),
            id=self.id,
            flags=flags,
            dlc=self.dlc,
            sdt=self.sdt,
            vcid=self.vcid,
            af=self.af,
            data= silkitapi.SilKit_ByteVector.from_sequence(self.data)
        )

class SilKitCanController(object):
    @silkitapi.SilKit_CanStateChangeHandler_t
    @staticmethod
    @auto_context
    def on_state_change(self, controller, event):
        self.state = silkitapi.SilKitCanControllerState(event.contents.state)
        if self.state == silkitapi.SilKitCanControllerState.STARTED:
            pass
        print(f"CAN entered state: {silkitapi.SilKitCanControllerState(self.state)}")

    @silkitapi.SilKit_CanErrorStateChangeHandler_t
    @staticmethod
    @auto_context
    def on_error_state_change(self, controller, event):
        self.error_state = silkitapi.SilKitCanErrorState(event.contents.state)
        print(f"CAN entered error state: {self.error_state}")

    @silkitapi.SilKit_CanFrameTransmitHandler_t
    @staticmethod
    @auto_context
    def on_transmit(self, controller, event):
        timestamp = self.time_slave.get_timestamp()
        transmission_status = silkitapi.SilKitCanTransmitStatus(event.contents.status)
        if transmission_status == silkitapi.SilKitCanTransmitStatus.TRANSMITTED:
            can_frame = ctypes.cast(event.contents.userContext, silkitapi.SilKit_CanFrame_p).contents
            msg = CanMessage(
                can_frame.id,
                *can_frame.data.to_sequence(),
                is_can_fd=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.FDF),
                is_can_xl=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.XLF),
                timestamp=timestamp,
                is_remote_frame=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.RTR),
                is_rx_fame=False,
                bitrate_switch=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.BRS),
                error_state_indicator=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.ESI),
                sdt=can_frame.sdt,
                vcid=can_frame.vcid,
                af=can_frame.af
            )
            self.rx_queue.append(msg)

    @silkitapi.SilKit_CanFrameHandler_t
    @staticmethod
    @auto_context
    def on_msg(self, controller, event):
        self.participant.info("Recv Message") #Log something
        timestamp = self.time_slave.get_timestamp()
        can_frame = event.contents.frame.contents
        msg = CanMessage(
            can_frame.id,
            *can_frame.data.to_sequence(),
            is_can_fd=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.FDF),
            is_can_xl=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.XLF),
            timestamp=timestamp,
            is_remote_frame=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.RTR),
            is_rx_fame=True,
            bitrate_switch=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.BRS),
            error_state_indicator=bool(can_frame.flags & silkitapi.SilKitCanFrameFlag.ESI),
            sdt=can_frame.sdt,
            vcid=can_frame.vcid,
            af=can_frame.af
        )
        self.rx_queue.append(msg)

    def __init__(
        self,
        participant,
        name: str = None,
        network_name: str = "VIRTUAL",
        rx_queue_size: int = 2000,
        bitrate: int  = 500000,
        bitrate_fd: int  = 2000000,
        bitrate_xl: int  = 10000000,
    ):
        self.participant = participant
        if name is None:
            self.name = f"{participant.name}_can_{len(participant._can_controllers)}"
        else:
            self.name = name
        self.network_name = network_name
        #Create the actual instance
        self.instance = silkitapi.SilKit_CanController_p()
        silkitapi.SilKit_CanController_Create(
            ctypes.byref(self.instance),
            participant.instance,
            name.encode(),
            network_name.encode()
        )
        #Create the context
        self.rx_queue = collections.deque(maxlen=rx_queue_size)
        self.state = None
        self.error_state = None
        #Create the Subscriber to sync with the time master
        self.time_slave = SilKitTimeSlave(self.participant, self.name)
        #Wrap self into ctypes
        self.__self = py2ct(self)
        self.set_bitrate(bitrate, bitrate_fd, bitrate_xl)
        #Set Handlers
        self.__state_handler__ = silkitapi.SilKit_HandlerId()
        silkitapi.SilKit_CanController_AddStateChangeHandler(
            self.instance,
            self.__self,
            self.on_state_change,
            ctypes.byref(self.__state_handler__)
        )
        self.__error_state_handler__ = silkitapi.SilKit_HandlerId()
        silkitapi.SilKit_CanController_AddErrorStateChangeHandler(
            self.instance,
            self.__self,
            self.on_error_state_change,
            ctypes.byref(self.__error_state_handler__)
        )
        self.__transmit_handler__ = silkitapi.SilKit_HandlerId()
        silkitapi.SilKit_CanController_AddFrameTransmitHandler(
            self.instance,
            self.__self,
            self.on_transmit,
            silkitapi.SilKitCanTransmitStatus.DEFAULT_MASK,
            ctypes.byref(self.__transmit_handler__)
        )
        self.__recv_handler__ = silkitapi.SilKit_HandlerId()
        silkitapi.SilKit_CanController_AddFrameHandler(
            self.instance,
            self.__self,
            self.on_msg,
            silkitapi.SilKitDirection.RECV,
            ctypes.byref(self.__recv_handler__)
        )

    def set_bitrate(
        self,
        bitrate: int,
        bitrate_fd: int,
        bitrate_xl: int,
    ):
        silkitapi.SilKit_CanController_SetBaudRate(
            self.instance,
            bitrate,
            bitrate_fd,
            bitrate_xl
        )

    def start(self):
        silkitapi.SilKit_CanController_Start(self.instance)

    def stop(self):
        silkitapi.SilKit_CanController_Stop(self.instance)

    def sleep(self):
        silkitapi.SilKit_CanController_Sleep(self.instance)

    def reset(self):
        silkitapi.SilKit_CanController_Reset(self.instance)

    def send(self, message: CanMessage):
        can_frame = message.to_silkit()
        silkitapi.SilKit_CanController_SendFrame(self.instance, ctypes.byref(can_frame), ctypes.byref(can_frame))

    def recv(self):
        try:
            return self.rx_queue.popleft()
        except IndexError as error:
            raise silkitapi.SilKitError(
                -1,
                f"Rx queue of {self.name} is emtpy!",
                self.recv.__name__
            ) from error

    def wait_tx_ack(self, message):
        while True:
            try:
                msg = self.recv()
            except silkitapi.SilKitError:
                pass
            else:
                if msg.id == message.id:
                    return msg