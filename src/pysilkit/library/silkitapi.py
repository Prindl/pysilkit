# Copyright (c) 2022 Vector Informatik GmbH

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import ctypes
import enum
import pathlib
import sys

###### Types.h ######

class SilKit_ParticipantConfiguration(ctypes.Structure):
    _pack_ = 8
SilKit_ParticipantConfiguration_p = ctypes.POINTER(SilKit_ParticipantConfiguration)

class SilKit_Participant(ctypes.Structure):
    _pack_ = 8
SilKit_Participant_p = ctypes.POINTER(SilKit_Participant)

class SilKit_Vendor_Vector_SilKitRegistry(ctypes.Structure):
    _pack_ = 8
SilKit_Vendor_Vector_SilKitRegistry_p = ctypes.POINTER(SilKit_Vendor_Vector_SilKitRegistry)

class SilKit_Experimental_SystemController(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SystemController_p = ctypes.POINTER(SilKit_Experimental_SystemController)

SilKit_ReturnCode = ctypes.c_int32

class SiKitReturnCode(enum.IntEnum):
    def __str__(self):
       return self.name.replace("_", " ")
    SUCCESS = 0x0
    UNSPECIFIED_ERROR = 0x1
    NOT_SUPPORTED = 0x2
    NOT_IMPLEMENTED = 0x3
    BAD_PARAMETER = 0x4
    BUFFER_TOO_SMALL = 0x5
    TIMEOUT = 0x6
    UNSUPPORTED_SERVICE = 0x7
    WRONG_STATE = 0x8
    TYPECONVERSION_ERROR = 0x9
    CONFIGURATION_ERROR = 0xA
    PROTOCOL_ERROR = 0xB
    ASSERTION_ERROR = 0xC
    EXTENSION_ERROR = 0xD
    LOGIC_ERROR = 0xE
    LENGTH_ERROR = 0xF
    OUT_OF_RANGE_ERROR = 0x10

class SilKit_Version(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("MajorVersion", ctypes.c_ubyte),
        ("MinorVersion", ctypes.c_ubyte)
    ]

class SilKit_ByteVector(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
        ("size", ctypes.c_size_t)
    ]

    @staticmethod
    def from_sequence(sequence):
        length = len(sequence)
        c_array = (ctypes.c_ubyte * length)(*sequence)
        return SilKit_ByteVector(
            data = ctypes.cast(c_array, ctypes.POINTER(ctypes.c_ubyte)),
            size = length
        )

    def to_sequence(self):
        return [self.data[i] for i in range(self.size)]

    def __str__(self):
        tmp = ", ".join([f"0x{self.data[i]:02X}" for i in range(self.size)])
        return f"[{tmp}]"

SilKit_LabelKind = ctypes.c_uint32
class SilKitLabelKind(enum.IntEnum):
    UNDEFINED = 0x0
    OPTIONAL = 0x1
    MANDATORY = 0x2

class SilKit_Label(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("key",  ctypes.c_char_p),
        ("value",  ctypes.c_char_p),
        ("kind", SilKit_LabelKind)
    ]
SilKit_Label_p = ctypes.POINTER(SilKit_Label)

class SilKit_LabelList(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("numLabels", ctypes.c_uint64),
        ("labels", ctypes.POINTER(SilKit_Label))
    ]

    @staticmethod
    def from_dict(**labels):
        sequence = [
            SilKit_Label(
                key=k.encode(),
                value=v.encode(),
                kind=SilKitLabelKind.MANDATORY
            ) for k, v in labels.items()
        ]
        label_list = (SilKit_Label * len(sequence))(*sequence)
        return SilKit_LabelList(numLabels=len(sequence), labels=ctypes.cast(label_list, SilKit_Label_p))

class SilKit_StringList(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("numStrings", ctypes.c_uint64),
        ("strings", ctypes.POINTER(ctypes.c_char_p))
    ]

SilKit_Bool = ctypes.c_bool
SilKit_True = 1
SilKit_False = 0

SilKit_Direction = ctypes.c_ubyte
class SilKitDirection(enum.IntEnum):
    UNDEFINED = 0
    SEND = 1
    RECV = 2
    SENDRECV = 3

SilKit_HandlerId = ctypes.c_uint64

###### Macros.h ######

BIT = lambda x: 1 << x
# SILKIT_UNUSED_ARG = lambda x: None

###### VersionMacros.h ######

GIT_HASH = "302cbdb8952f53224c4400fb442ab2699c707721"
VERSION_MAJOR = 4
VERSION_MINOR = 0
VERSION_PATCH = 55
BUILD_NUMBER = 0
VERSION_STRING = "4.0.55"
VERSION_SUFFIX = ""

###### Version.h ######

class SilKitError(Exception):
    def __init__(self, error_code, error_text, function_name):
        super(SilKitError, self).__init__(
            f"Error {error_code}: {function_name} failed ({error_text})"
        )
        self._args = error_code, error_text, function_name
        self.error_code, self.error_text, self.function_name = self._args

    def __reduce__(self):
        return type(self), self._args

if sys.maxsize > 2**32:
    __LIB_NAME = "SilKit64.dll"
else:
    __LIB_NAME = "SilKit.dll"

__LOADER = ctypes.windll
_file_path = pathlib.Path(__file__)
lib_folder = _file_path.parent.resolve()
__LOCAL_LIB = lib_folder / __LIB_NAME
try:
    _silkit_ = __LOADER.LoadLibrary(str(__LOCAL_LIB))
except FileNotFoundError as load_error:
    if getattr(sys, "frozen", False):
        ERROR_TEXT = "Failed to load Vector SilKit. Ensure the .exe is bundled with the '--collect-data' option"
    else:
        ERROR_TEXT = "Failed to load Vector SilKit."
    raise SilKitError(
        -1,
        ERROR_TEXT,
        __LOADER.LoadLibrary.__name__
    ) from load_error

def check_silkit_status(res, fnc, args):
    result = SiKitReturnCode(res)
    if result != SiKitReturnCode.SUCCESS:
        raise SilKitError(result, result.name, fnc.__name__)
    return result

SilKit_Version_Major = _silkit_.SilKit_Version_Major
SilKit_Version_Major.restype = SilKit_ReturnCode
SilKit_Version_Major.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
SilKit_Version_Major.errcheck = check_silkit_status
SilKit_Version_Major_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.POINTER(ctypes.c_uint32))

SilKit_Version_Minor = _silkit_.SilKit_Version_Minor
SilKit_Version_Minor.restype = SilKit_ReturnCode
SilKit_Version_Minor.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
SilKit_Version_Minor.errcheck = check_silkit_status
SilKit_Version_Minor_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.POINTER(ctypes.c_uint32))

SilKit_Version_Patch = _silkit_.SilKit_Version_Patch
SilKit_Version_Patch.restype = SilKit_ReturnCode
SilKit_Version_Patch.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
SilKit_Version_Patch.errcheck = check_silkit_status
SilKit_Version_Patch_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.POINTER(ctypes.c_uint32))

SilKit_Version_BuildNumber = _silkit_.SilKit_Version_BuildNumber
SilKit_Version_BuildNumber.restype = SilKit_ReturnCode
SilKit_Version_BuildNumber.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
SilKit_Version_BuildNumber.errcheck = check_silkit_status
SilKit_Version_BuildNumber_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.POINTER(ctypes.c_uint32))

SilKit_Version_String = _silkit_.SilKit_Version_String
SilKit_Version_String.restype = SilKit_ReturnCode
SilKit_Version_String.argtypes = [ctypes.c_char_p]
SilKit_Version_String.errcheck = check_silkit_status
SilKit_Version_String_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.c_char_p)

SilKit_Version_VersionSuffix = _silkit_.SilKit_Version_VersionSuffix
SilKit_Version_VersionSuffix.restype = SilKit_ReturnCode
SilKit_Version_VersionSuffix.argtypes = [ctypes.c_char_p]
SilKit_Version_VersionSuffix.errcheck = check_silkit_status
SilKit_Version_Suffix_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.c_char_p)

SilKit_Version_GitHash = _silkit_.SilKit_Version_GitHash
SilKit_Version_GitHash.restype = SilKit_ReturnCode
SilKit_Version_GitHash.argtypes = [ctypes.c_char_p]
SilKit_Version_GitHash.errcheck = check_silkit_status
SilKit_Version_GitHash_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, ctypes.c_char_p)

###### Logger.h ######

SilKit_LoggingLevel = ctypes.c_uint32
class SilKitLoggingLevel(enum.IntEnum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    CRITICAL = 5
    OFF = 0xFFFFFFFF

class SilKit_Logger(ctypes.Structure):
    _pack_ = 8
SilKit_Logger_p = ctypes.POINTER(SilKit_Logger)

SilKit_Logger_Log = _silkit_.SilKit_Logger_Log
SilKit_Logger_Log.restype = SilKit_ReturnCode
SilKit_Logger_Log.argtypes = [SilKit_Logger_p, SilKit_LoggingLevel, ctypes.c_char_p]
SilKit_Logger_Log.errcheck = check_silkit_status
SilKit_Logger_Log_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, SilKit_Logger_p, SilKit_LoggingLevel, ctypes.c_char_p)

SilKit_Logger_GetLogLevel = _silkit_.SilKit_Logger_GetLogLevel
SilKit_Logger_GetLogLevel.restype = SilKit_ReturnCode
SilKit_Logger_GetLogLevel.argtypes = [SilKit_Logger_p, ctypes.POINTER(SilKit_LoggingLevel)]
SilKit_Logger_GetLogLevel.errcheck = check_silkit_status
SilKit_Logger_GetLogLevel_t = ctypes.CFUNCTYPE(SilKit_ReturnCode, SilKit_Logger_p, ctypes.POINTER(SilKit_LoggingLevel))

###### Participant.h ######

SilKit_NanosecondsTime = ctypes.c_uint64
SilKit_NanosecondsWallclockTime = ctypes.c_uint64

SilKit_Participant_Create = _silkit_.SilKit_Participant_Create
SilKit_Participant_Create.restype = SilKit_ReturnCode
SilKit_Participant_Create.argtypes = [
    ctypes.POINTER(SilKit_Participant_p), 
    SilKit_ParticipantConfiguration_p, 
    ctypes.c_char_p, 
    ctypes.c_char_p
]
SilKit_Participant_Create.errcheck = check_silkit_status
SilKit_Participant_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode, 
    ctypes.POINTER(SilKit_Participant_p),
    SilKit_ParticipantConfiguration_p,
    ctypes.c_char_p,
    ctypes.c_char_p
)

SilKit_Participant_Destroy = _silkit_.SilKit_Participant_Destroy
SilKit_Participant_Destroy.restype = SilKit_ReturnCode
SilKit_Participant_Destroy.argtypes = [SilKit_Participant_p]
SilKit_Participant_Destroy.errcheck = check_silkit_status
SilKit_Participant_Destroy_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode, 
    SilKit_Participant_p
)

SilKit_Participant_GetLogger = _silkit_.SilKit_Participant_GetLogger
SilKit_Participant_GetLogger.restype = SilKit_ReturnCode
SilKit_Participant_GetLogger.argtypes = [
    ctypes.POINTER(SilKit_Logger_p), 
    SilKit_Participant_p
]
SilKit_Participant_GetLogger.errcheck = check_silkit_status
SilKit_Participant_GetLogger_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode, 
    ctypes.POINTER(SilKit_Logger_p), 
    SilKit_Participant_p
)

###### InterfaceIdentifiers.h ######

class SilKit_StructHeader(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint64),
        ("reserved", ctypes.c_uint64*3)
    ]

# The SK_ID_ macros are internal helpers. They are not to be used directly.
class SilKit_SK_ID_SERVICE(enum.IntEnum):
    START = 0
    CAN = 1
    ETHERNET = 2
    FLEXRAY = 3
    LIN = 4
    DATA = 5
    RPC = 6
    PARTICIPANT = 7
    NETWORK_SIMULATION = 8
    END = 9

SK_INVALID_DATATYPE_ID = 0
SK_INVALID_VERSION = 0

class SilKit_DATATYPE_ID(enum.IntEnum):
    CanFrame = 1
    CanFrameTransmitEvent = 2
    CanFrameEvent = 3
    CanStateChangeEvent = 4
    CanErrorStateChangeEvent = 5
    EthernetFrameEvent = 1
    EthernetFrameTransmitEvent = 2
    EthernetStateChangeEvent = 3
    EthernetBitrateChangeEvent = 4
    EthernetFrame = 5
    FlexrayFrameEvent = 1
    FlexrayFrameTransmitEvent = 2
    FlexraySymbolEvent = 3
    FlexraySymbolTransmitEvent = 5
    FlexrayCycleStartEvent = 6
    FlexrayPocStatusEvent = 7
    FlexrayWakeupEvent = 8
    FlexrayControllerConfig = 9
    FlexrayClusterParameters = 10
    FlexrayNodeParameters = 11
    FlexrayHostCommand = 12
    FlexrayHeader = 13
    FlexrayFrame = 14
    FlexrayTxBufferConfig = 15
    FlexrayTxBufferUpdate = 16
    LinFrame = 1
    LinFrameResponse = 2
    LinControllerConfig = 3
    LinFrameStatusEvent = 4
    LinGoToSleepEvent = 5
    LinWakeupEvent = 6
    Experimental_LinSlaveConfigurationEvent = 7
    Experimental_LinSlaveConfiguration = 8
    Experimental_LinControllerDynamicConfig = 9
    Experimental_LinFrameHeaderEvent = 10
    LinSendFrameHeaderRequest = 11
    DataMessageEvent = 1
    DataSpec = 2
    RpcCallEvent = 1
    RpcCallResultEvent = 2
    RpcSpec = 3
    ParticipantStatus = 1
    LifecycleConfiguration = 2
    WorkflowConfiguration = 3
    ParticipantConnectionInformation = 4
    Experimental_EventReceivers = 1
    Experimental_SimulatedNetworkFunctions = 2
    Experimental_SimulatedCanControllerFunctions = 3
    Experimental_SimulatedFlexRayControllerFunctions = 4
    Experimental_SimulatedEthernetControllerFunctions = 5
    Experimental_SimulatedLinControllerFunctions = 6
    Experimental_NetSim_CanConfigureBaudrate = 7
    Experimental_NetSim_CanControllerMode = 8
    Experimental_NetSim_CanFrameRequest = 9
    Experimental_NetSim_FlexrayControllerConfig = 10
    Experimental_NetSim_FlexrayHostCommand = 11
    Experimental_NetSim_FlexrayTxBufferConfigUpdate = 12
    Experimental_NetSim_FlexrayTxBufferUpdate = 13
    Experimental_NetSim_EthernetFrameRequest = 14
    Experimental_NetSim_EthernetControllerMode = 15
    Experimental_NetSim_LinFrameRequest = 16
    Experimental_NetSim_LinFrameHeaderRequest = 17
    Experimental_NetSim_LinWakeupPulse = 18
    Experimental_NetSim_LinControllerConfig = 19
    Experimental_NetSim_LinFrameResponseUpdate = 20
    Experimental_NetSim_LinControllerStatusUpdate = 21

class SilKit_VERSION(enum.IntEnum):
    CanFrame = 1
    CanFrameTransmitEvent = 2
    CanFrameEvent = 1
    CanStateChangeEvent = 1
    CanErrorStateChangeEvent = 1
    EthernetFrameEvent = 1
    EthernetFrameTransmitEvent = 1
    EthernetStateChangeEvent = 1
    EthernetBitrateChangeEvent = 1
    EthernetFrame = 1
    FlexrayFrameEvent = 1
    FlexrayFrameTransmitEvent = 1
    FlexraySymbolEvent = 1
    FlexraySymbolTransmitEvent = 1
    FlexrayCycleStartEvent = 1
    FlexrayPocStatusEvent = 1
    FlexrayWakeupEvent = 1
    FlexrayControllerConfig = 1
    FlexrayClusterParameters = 1
    FlexrayNodeParameters = 1
    FlexrayHostCommand = 1
    FlexrayHeader = 1
    FlexrayFrame = 1
    FlexrayTxBufferConfig = 1
    FlexrayTxBufferUpdate = 1
    LinFrame = 1
    LinFrameResponse = 1
    LinControllerConfig = 1
    LinFrameStatusEvent = 1
    LinGoToSleepEvent = 1
    LinWakeupEvent = 1
    Experimental_LinSlaveConfigurationEvent = 1
    Experimental_LinSlaveConfiguration = 1
    Experimental_LinControllerDynamicConfig = 1
    Experimental_LinFrameHeaderEvent = 1
    LinSendFrameHeaderRequest = 1
    DataMessageEvent = 1
    DataSpec = 1
    RpcCallEvent = 1
    RpcCallResultEvent = 1
    RpcSpec = 1
    ParticipantStatus = 1
    LifecycleConfiguration = 1
    WorkflowConfiguration = 3
    ParticipantConnectionInformation = 1
    Experimental_EventReceivers = 1
    Experimental_SimulatedNetworkFunctions = 1
    Experimental_SimulatedCanControllerFunctions = 1
    Experimental_SimulatedFlexRayControllerFunctions = 1
    Experimental_SimulatedEthernetControllerFunctions = 1
    Experimental_SimulatedLinControllerFunctions = 1
    Experimental_NetSim_CanConfigureBaudrate = 1
    Experimental_NetSim_CanControllerMode = 1
    Experimental_NetSim_CanFrameRequest = 1
    Experimental_NetSim_FlexrayControllerConfig = 1
    Experimental_NetSim_FlexrayHostCommand = 1
    Experimental_NetSim_FlexrayTxBufferConfigUpdate = 1
    Experimental_NetSim_FlexrayTxBufferUpdate = 1
    Experimental_NetSim_EthernetFrameRequest = 1
    Experimental_NetSim_EthernetControllerMode = 1
    Experimental_NetSim_LinFrameRequest = 1
    Experimental_NetSim_LinFrameHeaderRequest = 1
    Experimental_NetSim_LinWakeupPulse = 1
    Experimental_NetSim_LinControllerConfig = 1
    Experimental_NetSim_LinFrameResponseUpdate = 1
    Experimental_NetSim_LinControllerStatusUpdate = 1

SK_ID_GET_SERVICE = lambda id: id>>40 & 0xFF
SK_ID_GET_DATATYPE = lambda id: id>>40 & 0xFF
SK_ID_GET_VERSION = lambda id: id>>40 & 0xFF

def SK_ID_MAKE(service_name, datatype_name):
    if isinstance(service_name, str):
        service_id = SilKit_SK_ID_SERVICE[service_name]
    else:
        service_id = service_name
    return (
        83<<56 | #S
        75<<48 | #K
        service_id<<40 |
        SilKit_DATATYPE_ID[datatype_name]<<32 |
        SilKit_VERSION[datatype_name]<< 24
    )

def SK_ID_IS_VALID(sk_id):
    return (
        SilKit_SK_ID_SERVICE.START < SK_ID_GET_SERVICE(sk_id) < SilKit_SK_ID_SERVICE.END and
        SK_ID_GET_DATATYPE(sk_id) != SK_INVALID_DATATYPE_ID and
        SK_ID_GET_VERSION(sk_id) != SK_INVALID_VERSION and
        sk_id>>56 & 0xFF == 83 and sk_id>>48 & 0xFF == 75
    )

#define SilKit_Struct_GetHeader(VALUE) ((VALUE).structHeader)
#define SilKit_Struct_GetId(VALUE) (SilKit_Struct_GetHeader(VALUE).version)

class SilKit_STRUCT_VERSION(enum.IntEnum):
    CanFrame = SK_ID_MAKE(SilKit_SK_ID_SERVICE.CAN, "CanFrame")
    CanFrameTransmitEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.CAN, "CanFrameTransmitEvent")
    CanFrameEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.CAN, "CanFrameEvent")
    CanStateChangeEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.CAN, "CanStateChangeEvent")
    CanErrorStateChangeEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.CAN, "CanErrorStateChangeEvent")
    EthernetFrameEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.ETHERNET, "EthernetFrameEvent")
    EthernetFrameTransmitEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.ETHERNET, "EthernetFrameTransmitEvent")
    EthernetStateChangeEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.ETHERNET, "EthernetStateChangeEvent")
    EthernetBitrateChangeEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.ETHERNET, "EthernetBitrateChangeEvent")
    EthernetFrame = SK_ID_MAKE(SilKit_SK_ID_SERVICE.ETHERNET, "EthernetFrame")
    FlexrayFrameEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayFrameEvent")
    FlexrayFrameTransmitEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayFrameTransmitEvent")
    FlexraySymbolEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexraySymbolEvent")
    FlexraySymbolTransmitEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexraySymbolTransmitEvent")
    FlexrayCycleStartEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayCycleStartEvent")
    FlexrayPocStatusEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayPocStatusEvent")
    FlexrayWakeupEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayWakeupEvent")
    FlexrayControllerConfig = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayControllerConfig")
    FlexrayClusterParameters = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayClusterParameters")
    FlexrayNodeParameters = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayNodeParameters")
    FlexrayHostCommand = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayHostCommand")
    FlexrayHeader = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayHeader")
    FlexrayFrame = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayFrame")
    FlexrayTxBufferConfig = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayTxBufferConfig")
    FlexrayTxBufferUpdate = SK_ID_MAKE(SilKit_SK_ID_SERVICE.FLEXRAY, "FlexrayTxBufferUpdate")
    LinFrame = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinFrame")
    LinFrameResponse = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinFrameResponse")
    LinControllerConfig = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinControllerConfig")
    LinFrameStatusEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinFrameStatusEvent")
    LinGoToSleepEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinGoToSleepEvent")
    LinWakeupEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinWakeupEvent")
    Experimental_LinSlaveConfigurationEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "Experimental_LinSlaveConfigurationEvent")
    Experimental_LinSlaveConfiguration = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "Experimental_LinSlaveConfiguration")
    Experimental_LinControllerDynamicConfig = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "Experimental_LinControllerDynamicConfig")
    Experimental_LinFrameHeaderEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "Experimental_LinFrameHeaderEvent")
    LinSendFrameHeaderRequest = SK_ID_MAKE(SilKit_SK_ID_SERVICE.LIN, "LinSendFrameHeaderRequest")
    DataMessageEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.DATA, "DataMessageEvent")
    DataSpec = SK_ID_MAKE(SilKit_SK_ID_SERVICE.DATA, "DataSpec")
    RpcCallEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.RPC, "RpcCallEvent")
    RpcCallResultEvent = SK_ID_MAKE(SilKit_SK_ID_SERVICE.RPC, "RpcCallResultEvent")
    RpcSpec = SK_ID_MAKE(SilKit_SK_ID_SERVICE.RPC, "RpcSpec")
    ParticipantStatus = SK_ID_MAKE(SilKit_SK_ID_SERVICE.PARTICIPANT, "ParticipantStatus")
    LifecycleConfiguration = SK_ID_MAKE(SilKit_SK_ID_SERVICE.PARTICIPANT, "LifecycleConfiguration")
    WorkflowConfiguration = SK_ID_MAKE(SilKit_SK_ID_SERVICE.PARTICIPANT, "WorkflowConfiguration")
    ParticipantConnectionInformation = SK_ID_MAKE(SilKit_SK_ID_SERVICE.PARTICIPANT, "ParticipantConnectionInformation")
    Experimental_EventReceivers = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_EventReceivers")
    Experimental_SimulatedNetworkFunctions = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_SimulatedNetworkFunctions")
    Experimental_SimulatedCanControllerFunctions = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_SimulatedCanControllerFunctions")
    Experimental_SimulatedFlexRayControllerFunctions = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_SimulatedFlexRayControllerFunctions")
    Experimental_SimulatedEthernetControllerFunctions = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_SimulatedEthernetControllerFunctions")
    Experimental_SimulatedLinControllerFunctions = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_SimulatedLinControllerFunctions")
    Experimental_NetSim_CanConfigureBaudrate = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_CanConfigureBaudrate")
    Experimental_NetSim_CanControllerMode = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_CanControllerMode")
    Experimental_NetSim_CanFrameRequest = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_CanFrameRequest")
    Experimental_NetSim_FlexrayControllerConfig = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_FlexrayControllerConfig")
    Experimental_NetSim_FlexrayHostCommand = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_FlexrayHostCommand")
    Experimental_NetSim_FlexrayTxBufferConfigUpdate = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_FlexrayTxBufferConfigUpdate")
    Experimental_NetSim_FlexrayTxBufferUpdate = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_FlexrayTxBufferUpdate")
    Experimental_NetSim_EthernetFrameRequest = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_EthernetFrameRequest")
    Experimental_NetSim_EthernetControllerMode = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_EthernetControllerMode")
    Experimental_NetSim_LinFrameRequest = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_LinFrameRequest")
    Experimental_NetSim_LinFrameHeaderRequest = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_LinFrameHeaderRequest")
    Experimental_NetSim_LinWakeupPulse = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_LinWakeupPulse")
    Experimental_NetSim_LinControllerConfig = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_LinControllerConfig")
    Experimental_NetSim_LinFrameResponseUpdate = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_LinFrameResponseUpdate")
    Experimental_NetSim_LinControllerStatusUpdate = SK_ID_MAKE(SilKit_SK_ID_SERVICE.NETWORK_SIMULATION, "Experimental_NetSim_LinControllerStatusUpdate")

###### Vendor.h ######

SilKit_Vendor_Vector_SilKitRegistry_Create = _silkit_.SilKit_Vendor_Vector_SilKitRegistry_Create
SilKit_Vendor_Vector_SilKitRegistry_Create.restype = SilKit_ReturnCode
SilKit_Vendor_Vector_SilKitRegistry_Create.argtypes = [
    ctypes.POINTER(SilKit_Vendor_Vector_SilKitRegistry_p),
    SilKit_ParticipantConfiguration_p
]
SilKit_Vendor_Vector_SilKitRegistry_Create.errcheck = check_silkit_status
SilKit_Vendor_Vector_SilKitRegistry_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Vendor_Vector_SilKitRegistry_p),
    SilKit_ParticipantConfiguration_p
)

SilKit_Vendor_Vector_SilKitRegistry_Destroy = _silkit_.SilKit_Vendor_Vector_SilKitRegistry_Destroy
SilKit_Vendor_Vector_SilKitRegistry_Destroy.restype = SilKit_ReturnCode
SilKit_Vendor_Vector_SilKitRegistry_Destroy.argtypes = [
    SilKit_Vendor_Vector_SilKitRegistry_p,
]
SilKit_Vendor_Vector_SilKitRegistry_Destroy.errcheck = check_silkit_status
SilKit_Vendor_Vector_SilKitRegistry_Destroy_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Vendor_Vector_SilKitRegistry_p
)

SilKit_Vendor_Vector_SilKitRegistry_AllDisconnectedHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.c_void_p,
    SilKit_Vendor_Vector_SilKitRegistry_p
)

SilKit_Vendor_Vector_SilKitRegistry_SetAllDisconnectedHandler = _silkit_.SilKit_Vendor_Vector_SilKitRegistry_SetAllDisconnectedHandler
SilKit_Vendor_Vector_SilKitRegistry_SetAllDisconnectedHandler.restype = SilKit_ReturnCode
SilKit_Vendor_Vector_SilKitRegistry_SetAllDisconnectedHandler.argtypes = [
    SilKit_Vendor_Vector_SilKitRegistry_p,
    ctypes.c_void_p,
    SilKit_Vendor_Vector_SilKitRegistry_AllDisconnectedHandler_t,
]
SilKit_Vendor_Vector_SilKitRegistry_SetAllDisconnectedHandler.errcheck = check_silkit_status
SilKit_Vendor_Vector_SilKitRegistry_SetAllDisconnectedHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Vendor_Vector_SilKitRegistry_p,
    ctypes.c_void_p,
    SilKit_Vendor_Vector_SilKitRegistry_AllDisconnectedHandler_t
)

SilKit_Vendor_Vector_SilKitRegistry_GetLogger = _silkit_.SilKit_Vendor_Vector_SilKitRegistry_GetLogger
SilKit_Vendor_Vector_SilKitRegistry_GetLogger.restype = SilKit_ReturnCode
SilKit_Vendor_Vector_SilKitRegistry_GetLogger.argtypes = [
    ctypes.POINTER(SilKit_Logger_p),
    SilKit_Vendor_Vector_SilKitRegistry_p,
]
SilKit_Vendor_Vector_SilKitRegistry_GetLogger.errcheck = check_silkit_status
SilKit_Vendor_Vector_SilKitRegistry_GetLogger_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Logger_p),
    SilKit_Vendor_Vector_SilKitRegistry_p
)

SilKit_Vendor_Vector_SilKitRegistry_StartListening = _silkit_.SilKit_Vendor_Vector_SilKitRegistry_StartListening
SilKit_Vendor_Vector_SilKitRegistry_StartListening.restype = SilKit_ReturnCode
SilKit_Vendor_Vector_SilKitRegistry_StartListening.argtypes = [
    SilKit_Vendor_Vector_SilKitRegistry_p,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_char_p),
]
SilKit_Vendor_Vector_SilKitRegistry_StartListening.errcheck = check_silkit_status
SilKit_Vendor_Vector_SilKitRegistry_StartListening_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Vendor_Vector_SilKitRegistry_p,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_char_p)
)

###### SilKit.h ######

SilKit_ReturnCodeToString = _silkit_.SilKit_ReturnCodeToString
SilKit_ReturnCodeToString.restype = SilKit_ReturnCode
SilKit_ReturnCodeToString.argtypes = [
    ctypes.POINTER(ctypes.c_char_p),
    SilKit_ReturnCode
]
SilKit_ReturnCodeToString.errcheck = check_silkit_status
SilKit_ReturnCodeToString_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(ctypes.c_char_p),
    SilKit_ReturnCode
)

SilKit_GetLastErrorString = _silkit_.SilKit_GetLastErrorString
SilKit_GetLastErrorString.restype = ctypes.c_char_p
SilKit_GetLastErrorString.argtypes = []
SilKit_GetLastErrorString_t = ctypes.CFUNCTYPE(ctypes.c_char_p)

SilKit_ParticipantConfiguration_FromString = _silkit_.SilKit_ParticipantConfiguration_FromString
SilKit_ParticipantConfiguration_FromString.restype = SilKit_ReturnCode
SilKit_ParticipantConfiguration_FromString.argtypes = [
    ctypes.POINTER(SilKit_ParticipantConfiguration_p),
    ctypes.c_char_p
]
SilKit_ParticipantConfiguration_FromString.errcheck = check_silkit_status
SilKit_ParticipantConfiguration_FromString_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_ParticipantConfiguration_p),
    ctypes.c_char_p
)

SilKit_ParticipantConfiguration_FromFile = _silkit_.SilKit_ParticipantConfiguration_FromFile
SilKit_ParticipantConfiguration_FromFile.restype = SilKit_ReturnCode
SilKit_ParticipantConfiguration_FromFile.argtypes = [
    ctypes.POINTER(SilKit_ParticipantConfiguration_p),
    ctypes.c_char_p
]
SilKit_ParticipantConfiguration_FromFile.errcheck = check_silkit_status
SilKit_ParticipantConfiguration_FromFile_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_ParticipantConfiguration_p),
    ctypes.c_char_p
)

SilKit_ParticipantConfiguration_Destroy = _silkit_.SilKit_ParticipantConfiguration_Destroy
SilKit_ParticipantConfiguration_Destroy.restype = SilKit_ReturnCode
SilKit_ParticipantConfiguration_Destroy.argtypes = [
    SilKit_ParticipantConfiguration_p
]
SilKit_ParticipantConfiguration_Destroy.errcheck = check_silkit_status
SilKit_ParticipantConfiguration_Destroy_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_ParticipantConfiguration_p
)

###### Orchestration.h ######

SilKit_ParticipantState = ctypes.c_int16
class SilKitParticipantState(enum.IntEnum):
    INVALID = 0
    SERVICES_CREATED = 10
    COMMUNICATION_INITIALIZING = 20
    COMMUNICATION_INITIALIZED = 30
    READY_TO_RUN = 40
    RUNNING = 50
    PAUSED = 60
    STOPPING = 70
    STOPPED = 80
    ERROR = 90
    SHUTTING_DOWN = 100
    SHUTDOWN = 110
    ABORTING = 120

SilKit_SystemState = ctypes.c_int16
class SilKitSystemState(enum.IntEnum):
    INVALID = 0
    SERVICES_CREATED = 10
    COMMUNICATION_INITIALIZING = 20
    COMMUNICATION_INITIALIZED = 30
    READY_TO_RUN = 40
    RUNNING = 50
    PAUSED = 60
    STOPPING = 70
    STOPPED = 80
    ERROR = 90
    SHUTTING_DOWN = 100
    SHUTDOWN = 110
    ABORTING = 120

SilKit_OperationMode = ctypes.c_byte
class SilKitOperationMode(enum.IntEnum):
    INVALID = 0
    COORDINATED = 10
    AUTONOMOUS = 20

class SilKit_ParticipantStatus(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("participantName", ctypes.c_char_p),
        ("participantState", SilKit_ParticipantState),
        ("enterReason", ctypes.c_char_p),
        ("enterTime", SilKit_NanosecondsWallclockTime),
        ("refreshTime", SilKit_NanosecondsWallclockTime)
    ]
SilKit_ParticipantStatus_p = ctypes.POINTER(SilKit_ParticipantStatus)

class SilKit_WorkflowConfiguration(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("requiredParticipantNames", ctypes.POINTER(SilKit_StringList))
    ]
SilKit_WorkflowConfiguration_p = ctypes.POINTER(SilKit_WorkflowConfiguration)

class SilKit_LifecycleConfiguration(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("operationMode", SilKit_OperationMode)
    ]
SilKit_LifecycleConfiguration_p = ctypes.POINTER(SilKit_LifecycleConfiguration)

class SilKit_SystemMonitor(ctypes.Structure):
    _pack_ = 8
SilKit_SystemMonitor_p = ctypes.POINTER(SilKit_SystemMonitor)

class SilKit_LifecycleService(ctypes.Structure):
    _pack_ = 8
SilKit_LifecycleService_p = ctypes.POINTER(SilKit_LifecycleService)

class SilKit_TimeSyncService(ctypes.Structure):
    _pack_ = 8
SilKit_TimeSyncService_p = ctypes.POINTER(SilKit_TimeSyncService)

SilKit_LifecycleService_Create = _silkit_.SilKit_LifecycleService_Create
SilKit_LifecycleService_Create.restype = SilKit_ReturnCode
SilKit_LifecycleService_Create.argtypes = [
    ctypes.POINTER(SilKit_LifecycleService_p),
    SilKit_Participant_p,
    SilKit_LifecycleConfiguration_p,
]
SilKit_LifecycleService_Create.errcheck = check_silkit_status
SilKit_LifecycleService_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_LifecycleService_p),
    SilKit_Participant_p,
    SilKit_LifecycleConfiguration_p
)

SilKit_LifecycleService_CommunicationReadyHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_SetCommunicationReadyHandler = _silkit_.SilKit_LifecycleService_SetCommunicationReadyHandler
SilKit_LifecycleService_SetCommunicationReadyHandler.restype = SilKit_ReturnCode
SilKit_LifecycleService_SetCommunicationReadyHandler.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_CommunicationReadyHandler_t
]
SilKit_LifecycleService_SetCommunicationReadyHandler.errcheck = check_silkit_status
SilKit_LifecycleService_SetCommunicationReadyHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_CommunicationReadyHandler_t
)

SilKit_LifecycleService_SetCommunicationReadyHandlerAsync = _silkit_.SilKit_LifecycleService_SetCommunicationReadyHandlerAsync
SilKit_LifecycleService_SetCommunicationReadyHandlerAsync.restype = SilKit_ReturnCode
SilKit_LifecycleService_SetCommunicationReadyHandlerAsync.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_CommunicationReadyHandler_t
]
SilKit_LifecycleService_SetCommunicationReadyHandlerAsync.errcheck = check_silkit_status
SilKit_LifecycleService_SetCommunicationReadyHandlerAsync_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_CommunicationReadyHandler_t
)

SilKit_LifecycleService_CompleteCommunicationReadyHandlerAsync = _silkit_.SilKit_LifecycleService_CompleteCommunicationReadyHandlerAsync
SilKit_LifecycleService_CompleteCommunicationReadyHandlerAsync.restype = SilKit_ReturnCode
SilKit_LifecycleService_CompleteCommunicationReadyHandlerAsync.argtypes = [
    SilKit_LifecycleService_p
]
SilKit_LifecycleService_CompleteCommunicationReadyHandlerAsync.errcheck = check_silkit_status
SilKit_LifecycleService_CompleteCommunicationReadyHandlerAsync_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_StartingHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_SetStartingHandler = _silkit_.SilKit_LifecycleService_SetStartingHandler
SilKit_LifecycleService_SetStartingHandler.restype = SilKit_ReturnCode
SilKit_LifecycleService_SetStartingHandler.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_StartingHandler_t
]
SilKit_LifecycleService_SetStartingHandler.errcheck = check_silkit_status
SilKit_LifecycleService_SetStartingHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_StartingHandler_t
)

SilKit_LifecycleService_StopHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_SetStopHandler = _silkit_.SilKit_LifecycleService_SetStopHandler
SilKit_LifecycleService_SetStopHandler.restype = SilKit_ReturnCode
SilKit_LifecycleService_SetStopHandler.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_StopHandler_t
]
SilKit_LifecycleService_SetStopHandler.errcheck = check_silkit_status
SilKit_LifecycleService_SetStopHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_StopHandler_t
)

SilKit_LifecycleService_ShutdownHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_SetShutdownHandler = _silkit_.SilKit_LifecycleService_SetShutdownHandler
SilKit_LifecycleService_SetShutdownHandler.restype = SilKit_ReturnCode
SilKit_LifecycleService_SetShutdownHandler.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_ShutdownHandler_t
]
SilKit_LifecycleService_SetShutdownHandler.errcheck = check_silkit_status
SilKit_LifecycleService_SetShutdownHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_ShutdownHandler_t
)

SilKit_LifecycleService_AbortHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LifecycleService_p,
    SilKit_ParticipantState
)

SilKit_LifecycleService_SetAbortHandler = _silkit_.SilKit_LifecycleService_SetAbortHandler
SilKit_LifecycleService_SetAbortHandler.restype = SilKit_ReturnCode
SilKit_LifecycleService_SetAbortHandler.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_AbortHandler_t
]
SilKit_LifecycleService_SetAbortHandler.errcheck = check_silkit_status
SilKit_LifecycleService_SetAbortHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_void_p,
    SilKit_LifecycleService_AbortHandler_t
)

SilKit_LifecycleService_StartLifecycle = _silkit_.SilKit_LifecycleService_StartLifecycle
SilKit_LifecycleService_StartLifecycle.restype = SilKit_ReturnCode
SilKit_LifecycleService_StartLifecycle.argtypes = [
    SilKit_LifecycleService_p,
]
SilKit_LifecycleService_StartLifecycle.errcheck = check_silkit_status
SilKit_LifecycleService_StartLifecycle_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_WaitForLifecycleToComplete = _silkit_.SilKit_LifecycleService_WaitForLifecycleToComplete
SilKit_LifecycleService_WaitForLifecycleToComplete.restype = SilKit_ReturnCode
SilKit_LifecycleService_WaitForLifecycleToComplete.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.POINTER(SilKit_ParticipantState)
]
SilKit_LifecycleService_WaitForLifecycleToComplete.errcheck = check_silkit_status
SilKit_LifecycleService_WaitForLifecycleToComplete_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.POINTER(SilKit_ParticipantState)
)

SilKit_LifecycleService_ReportError = _silkit_.SilKit_LifecycleService_ReportError
SilKit_LifecycleService_ReportError.restype = SilKit_ReturnCode
SilKit_LifecycleService_ReportError.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_char_p
]
SilKit_LifecycleService_ReportError.errcheck = check_silkit_status
SilKit_LifecycleService_ReportError_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_char_p
)

SilKit_LifecycleService_Pause = _silkit_.SilKit_LifecycleService_Pause
SilKit_LifecycleService_Pause.restype = SilKit_ReturnCode
SilKit_LifecycleService_Pause.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_char_p
]
SilKit_LifecycleService_Pause.errcheck = check_silkit_status
SilKit_LifecycleService_Pause_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_char_p
)

SilKit_LifecycleService_Continue = _silkit_.SilKit_LifecycleService_Continue
SilKit_LifecycleService_Continue.restype = SilKit_ReturnCode
SilKit_LifecycleService_Continue.argtypes = [
    SilKit_LifecycleService_p
]
SilKit_LifecycleService_Continue.errcheck = check_silkit_status

SilKit_LifecycleService_Continue_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_Stop = _silkit_.SilKit_LifecycleService_Stop
SilKit_LifecycleService_Stop.restype = SilKit_ReturnCode
SilKit_LifecycleService_Stop.argtypes = [
    SilKit_LifecycleService_p,
    ctypes.c_char_p
]
SilKit_LifecycleService_Stop.errcheck = check_silkit_status
SilKit_LifecycleService_Stop_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LifecycleService_p,
    ctypes.c_char_p
)

SilKit_LifecycleService_State = _silkit_.SilKit_LifecycleService_State
SilKit_LifecycleService_State.restype = SilKit_ReturnCode
SilKit_LifecycleService_State.argtypes = [
    ctypes.POINTER(SilKit_ParticipantState),
    SilKit_LifecycleService_p
]
SilKit_LifecycleService_State.errcheck = check_silkit_status
SilKit_LifecycleService_State_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_ParticipantState),
    SilKit_LifecycleService_p
)

SilKit_LifecycleService_Status = _silkit_.SilKit_LifecycleService_Status
SilKit_LifecycleService_Status.restype = SilKit_ReturnCode
SilKit_LifecycleService_Status.argtypes = [
    SilKit_ParticipantStatus_p,
    SilKit_LifecycleService_p
]
SilKit_LifecycleService_Status.errcheck = check_silkit_status
SilKit_LifecycleService_Status_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_ParticipantStatus_p,
    SilKit_LifecycleService_p
)

SilKit_TimeSyncService_Create = _silkit_.SilKit_TimeSyncService_Create
SilKit_TimeSyncService_Create.restype = SilKit_ReturnCode
SilKit_TimeSyncService_Create.argtypes = [
    ctypes.POINTER(SilKit_TimeSyncService_p),
    SilKit_LifecycleService_p
]
SilKit_TimeSyncService_Create.errcheck = check_silkit_status
SilKit_TimeSyncService_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_TimeSyncService_p),
    SilKit_LifecycleService_p
)

SilKit_TimeSyncService_SimulationStepHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_TimeSyncService_p,
    SilKit_NanosecondsTime,
    SilKit_NanosecondsTime
)

SilKit_TimeSyncService_SetSimulationStepHandler = _silkit_.SilKit_TimeSyncService_SetSimulationStepHandler
SilKit_TimeSyncService_SetSimulationStepHandler.restype = SilKit_ReturnCode
SilKit_TimeSyncService_SetSimulationStepHandler.argtypes = [
    SilKit_TimeSyncService_p,
    ctypes.c_void_p,
    SilKit_TimeSyncService_SimulationStepHandler_t,
    SilKit_NanosecondsTime
]
SilKit_TimeSyncService_SetSimulationStepHandler.errcheck = check_silkit_status
SilKit_TimeSyncService_SetSimulationStepHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_TimeSyncService_p,
    ctypes.c_void_p,
    SilKit_TimeSyncService_SimulationStepHandler_t,
    SilKit_NanosecondsTime
)

SilKit_TimeSyncService_SetSimulationStepHandlerAsync = _silkit_.SilKit_TimeSyncService_SetSimulationStepHandlerAsync
SilKit_TimeSyncService_SetSimulationStepHandlerAsync.restype = SilKit_ReturnCode
SilKit_TimeSyncService_SetSimulationStepHandlerAsync.argtypes = [
    SilKit_TimeSyncService_p,
    ctypes.c_void_p,
    SilKit_TimeSyncService_SimulationStepHandler_t,
    SilKit_NanosecondsTime
]
SilKit_TimeSyncService_SetSimulationStepHandlerAsync.errcheck = check_silkit_status
SilKit_TimeSyncService_SetSimulationStepHandlerAsync_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_TimeSyncService_p,
    ctypes.c_void_p,
    SilKit_TimeSyncService_SimulationStepHandler_t,
    SilKit_NanosecondsTime
)

SilKit_TimeSyncService_CompleteSimulationStep = _silkit_.SilKit_TimeSyncService_CompleteSimulationStep
SilKit_TimeSyncService_CompleteSimulationStep.restype = SilKit_ReturnCode
SilKit_TimeSyncService_CompleteSimulationStep.argtypes = [
    SilKit_TimeSyncService_p
]
SilKit_TimeSyncService_CompleteSimulationStep.errcheck = check_silkit_status
SilKit_TimeSyncService_CompleteSimulationStep_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_TimeSyncService_p
)

SilKit_TimeSyncService_Now = _silkit_.SilKit_TimeSyncService_Now
SilKit_TimeSyncService_Now.restype = SilKit_ReturnCode
SilKit_TimeSyncService_Now.argtypes = [
    SilKit_TimeSyncService_p,
    ctypes.POINTER(SilKit_NanosecondsTime)
]
SilKit_TimeSyncService_Now.errcheck = check_silkit_status
SilKit_TimeSyncService_Now_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_TimeSyncService_p,
    ctypes.POINTER(SilKit_NanosecondsTime)
)

SilKit_SystemMonitor_Create = _silkit_.SilKit_SystemMonitor_Create
SilKit_SystemMonitor_Create.restype = SilKit_ReturnCode
SilKit_SystemMonitor_Create.argtypes = [
    ctypes.POINTER(SilKit_SystemMonitor_p),
    SilKit_Participant_p
]
SilKit_SystemMonitor_Create.errcheck = check_silkit_status
SilKit_SystemMonitor_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_SystemMonitor_p),
    SilKit_Participant_p
)

SilKit_SystemMonitor_GetParticipantStatus = _silkit_.SilKit_SystemMonitor_GetParticipantStatus
SilKit_SystemMonitor_GetParticipantStatus.restype = SilKit_ReturnCode
SilKit_SystemMonitor_GetParticipantStatus.argtypes = [
    SilKit_ParticipantStatus_p,
    SilKit_SystemMonitor_p,
    ctypes.c_char_p
]
SilKit_SystemMonitor_GetParticipantStatus.errcheck = check_silkit_status
SilKit_SystemMonitor_GetParticipantStatus_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_ParticipantStatus_p,
    SilKit_SystemMonitor_p,
    ctypes.c_char_p
)

SilKit_SystemMonitor_GetSystemState = _silkit_.SilKit_SystemMonitor_GetSystemState
SilKit_SystemMonitor_GetSystemState.restype = SilKit_ReturnCode
SilKit_SystemMonitor_GetSystemState.argtypes = [
    ctypes.POINTER(SilKit_SystemState),
    SilKit_SystemMonitor_p
]
SilKit_SystemMonitor_GetSystemState.errcheck = check_silkit_status
SilKit_SystemMonitor_GetSystemState_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_SystemState),
    SilKit_SystemMonitor_p
)

SilKit_SystemStateHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_SystemMonitor_p,
    SilKit_SystemState
)

SilKit_SystemMonitor_AddSystemStateHandler = _silkit_.SilKit_SystemMonitor_AddSystemStateHandler
SilKit_SystemMonitor_AddSystemStateHandler.restype = SilKit_ReturnCode
SilKit_SystemMonitor_AddSystemStateHandler.argtypes = [
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_SystemStateHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_SystemMonitor_AddSystemStateHandler.errcheck = check_silkit_status
SilKit_SystemMonitor_AddSystemStateHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_SystemStateHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_SystemMonitor_RemoveSystemStateHandler = _silkit_.SilKit_SystemMonitor_RemoveSystemStateHandler
SilKit_SystemMonitor_RemoveSystemStateHandler.restype = SilKit_ReturnCode
SilKit_SystemMonitor_RemoveSystemStateHandler.argtypes = [
    SilKit_SystemMonitor_p,
    SilKit_HandlerId
]
SilKit_SystemMonitor_RemoveSystemStateHandler.errcheck = check_silkit_status
SilKit_SystemMonitor_RemoveSystemStateHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    SilKit_HandlerId
)

SilKit_ParticipantStatusHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_SystemMonitor_p,
    ctypes.c_char_p,
    SilKit_ParticipantStatus_p
)

SilKit_SystemMonitor_AddParticipantStatusHandler = _silkit_.SilKit_SystemMonitor_AddParticipantStatusHandler
SilKit_SystemMonitor_AddParticipantStatusHandler.restype = SilKit_ReturnCode
SilKit_SystemMonitor_AddParticipantStatusHandler.argtypes = [
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_ParticipantStatusHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_SystemMonitor_AddParticipantStatusHandler.errcheck = check_silkit_status
SilKit_SystemMonitor_AddParticipantStatusHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_ParticipantStatusHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_SystemMonitor_RemoveParticipantStatusHandler = _silkit_.SilKit_SystemMonitor_RemoveParticipantStatusHandler
SilKit_SystemMonitor_RemoveParticipantStatusHandler.restype = SilKit_ReturnCode
SilKit_SystemMonitor_RemoveParticipantStatusHandler.argtypes = [
    SilKit_SystemMonitor_p,
    SilKit_HandlerId
]
SilKit_SystemMonitor_RemoveParticipantStatusHandler.errcheck = check_silkit_status
SilKit_SystemMonitor_RemoveParticipantStatusHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    SilKit_HandlerId
)

class SilKit_ParticipantConnectionInformation(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("participantName", ctypes.c_char_p)
    ]
SilKit_ParticipantConnectionInformation_p = ctypes.POINTER(SilKit_ParticipantConnectionInformation)

SilKit_SystemMonitor_ParticipantConnectedHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_SystemMonitor_p,
    SilKit_ParticipantConnectionInformation_p
)

SilKit_SystemMonitor_SetParticipantConnectedHandler = _silkit_.SilKit_SystemMonitor_SetParticipantConnectedHandler
SilKit_SystemMonitor_SetParticipantConnectedHandler.restype = SilKit_ReturnCode
SilKit_SystemMonitor_SetParticipantConnectedHandler.argtypes = [
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_SystemMonitor_ParticipantConnectedHandler_t
]
SilKit_SystemMonitor_SetParticipantConnectedHandler.errcheck = check_silkit_status
SilKit_SystemMonitor_SetParticipantConnectedHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_SystemMonitor_ParticipantConnectedHandler_t
)

SilKit_SystemMonitor_ParticipantDisconnectedHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_SystemMonitor_p,
    SilKit_ParticipantConnectionInformation_p
)

SilKit_SystemMonitor_SetParticipantDisconnectedHandler = _silkit_.SilKit_SystemMonitor_SetParticipantDisconnectedHandler
SilKit_SystemMonitor_SetParticipantDisconnectedHandler.restype = SilKit_ReturnCode
SilKit_SystemMonitor_SetParticipantDisconnectedHandler.argtypes = [
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_SystemMonitor_ParticipantDisconnectedHandler_t
]
SilKit_SystemMonitor_SetParticipantDisconnectedHandler.errcheck = check_silkit_status
SilKit_SystemMonitor_SetParticipantDisconnectedHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    ctypes.c_void_p,
    SilKit_SystemMonitor_ParticipantDisconnectedHandler_t
)

SilKit_SystemMonitor_IsParticipantConnected = _silkit_.SilKit_SystemMonitor_IsParticipantConnected
SilKit_SystemMonitor_IsParticipantConnected.restype = SilKit_ReturnCode
SilKit_SystemMonitor_IsParticipantConnected.argtypes = [
    SilKit_SystemMonitor_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_Bool)
]
SilKit_SystemMonitor_IsParticipantConnected.errcheck = check_silkit_status
SilKit_SystemMonitor_IsParticipantConnected_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_SystemMonitor_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_Bool)
)

SilKit_Experimental_SystemController_Create = _silkit_.SilKit_Experimental_SystemController_Create
SilKit_Experimental_SystemController_Create.restype = SilKit_ReturnCode
SilKit_Experimental_SystemController_Create.argtypes = [
    ctypes.POINTER(SilKit_Experimental_SystemController_p),
    SilKit_Participant_p
]
SilKit_Experimental_SystemController_Create.errcheck = check_silkit_status
SilKit_Experimental_SystemController_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Experimental_SystemController_p),
    SilKit_Participant_p
)

SilKit_Experimental_SystemController_AbortSimulation = _silkit_.SilKit_Experimental_SystemController_AbortSimulation
SilKit_Experimental_SystemController_AbortSimulation.restype = SilKit_ReturnCode
SilKit_Experimental_SystemController_AbortSimulation.argtypes = [
    SilKit_Experimental_SystemController_p
]
SilKit_Experimental_SystemController_AbortSimulation.errcheck = check_silkit_status
SilKit_Experimental_SystemController_AbortSimulation_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Experimental_SystemController_p
)

SilKit_Experimental_SystemController_SetWorkflowConfiguration = _silkit_.SilKit_Experimental_SystemController_SetWorkflowConfiguration
SilKit_Experimental_SystemController_SetWorkflowConfiguration.restype = SilKit_ReturnCode
SilKit_Experimental_SystemController_SetWorkflowConfiguration.argtypes = [
    SilKit_Experimental_SystemController_p,
    SilKit_WorkflowConfiguration_p
]
SilKit_Experimental_SystemController_SetWorkflowConfiguration.errcheck = check_silkit_status
SilKit_Experimental_SystemController_SetWorkflowConfiguration_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Experimental_SystemController_p,
    SilKit_WorkflowConfiguration_p
)

###### Can.h ######

SilKit_CanFrameFlag = ctypes.c_uint32
class SilKitCanFrameFlag(enum.IntFlag):
    IDE = BIT(9) # Identifier Extension
    RTR = BIT(4) # Remote Transmission Request
    FDF = BIT(12) # FD Format Indicator
    BRS = BIT(13) # Bit Rate Switch  (for FD Format only)
    ESI = BIT(14) # Error State indicator (for FD Format only)
    XLF = BIT(15) # XL Format Indicator
    SEC = BIT(16) # Simple Extended Content (for XL Format only)

class SilKit_CanFrame(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("id", ctypes.c_uint32), # CAN Identifier
        ("flags", SilKit_CanFrameFlag), # CAN Arbitration and Control Field Flags
        ("dlc", ctypes.c_uint16), # Data Length Code - determined by a network simulator if available
        ("sdt", ctypes.c_ubyte), # SDU type - describes the structure of the frames Data Field content (for XL Format only)
        ("vcid", ctypes.c_ubyte), # Virtual CAN network ID (for XL Format only)
        ("af", ctypes.c_uint32), # Acceptance field (for XL Format only)
        ("data", SilKit_ByteVector) # Data field containing the payload
    ]
SilKit_CanFrame_p = ctypes.POINTER(SilKit_CanFrame)

class SilKit_CanFrameEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Reception time
        ("frame", SilKit_CanFrame_p), # The CAN Frame that corresponds to the meta data
        ("direction", SilKit_Direction), # The transmit direction of the CAN frame (TX/RX)
        ("userContext", ctypes.c_void_p) # Optional pointer provided by user when sending the frame
    ]
SilKit_CanFrameEvent_p = ctypes.POINTER(SilKit_CanFrameEvent)

SilKit_CanTransmitStatus = ctypes.c_int32
class SilKitCanTransmitStatus(enum.IntEnum):
    TRANSMITTED = BIT(0)
    CANCELED = BIT(1)
    # BIT(3) is RESERVED (used to be DuplicatedTransmitId)
    TRANSMIT_QUEUE_FULL = BIT(2)
    DEFAULT_MASK = TRANSMITTED | CANCELED | TRANSMIT_QUEUE_FULL

class SilKit_CanFrameTransmitEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("userContext", ctypes.c_void_p), # Optional pointer provided by user when sending the frame
        ("timestamp", SilKit_NanosecondsTime), # Reception time
        ("status", SilKit_CanTransmitStatus), # Status of the CanTransmitRequest
        # Identifies the CAN id to which this CanFrameTransmitEvent refers to.
        #
        # version Check: SK_ID_GET_VERSION(SilKit_Struct_GetId(event)) >= 2
        #
        # You must check that the structure version is sufficient before accessing this field.
        # Added in SIL Kit version 4.0.11.
        ("canId", ctypes.c_uint32)
    ]
SilKit_CanFrameTransmitEvent_p = ctypes.POINTER(SilKit_CanFrameTransmitEvent)

SilKit_CanControllerState = ctypes.c_int32
class SilKitCanControllerState(enum.IntEnum):
    def __str__(self):
       return self.name.replace("_", " ")
    UNINIT = 0 # CAN controller is not initialized (initial state after reset).
    STOPPED = 1 # CAN controller is initialized but does not participate on the CAN bus.
    STARTED = 2 # CAN controller is in normal operation mode.
    SLEEP = 3 # CAN controller is in sleep mode which is similar to the Stopped state.

class SilKit_CanStateChangeEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Reception time
        ("state", SilKit_CanControllerState), # CAN controller state
    ]
SilKit_CanStateChangeEvent_p = ctypes.POINTER(SilKit_CanStateChangeEvent)

SilKit_CanErrorState = ctypes.c_int32
class SilKitCanErrorState(enum.IntEnum):
    def __str__(self):
       return self.name.replace("_", " ")
    # Error State is Not Available, because CAN controller is in state Uninit.
    NOT_AVAILABLE = 0
    # Error Active Mode, the CAN controller is allowed to send messages and active error flags.
    ERROR_ACTIVE = 1
    # Error Passive Mode, the CAN controller is still allowed to send messages, but must not send active error flags.
    ERROR_PASSIVE = 2
    # Bus Off Mode, the CAN controller does not take part in communication.
    BUS_OFF = 3

class SilKit_CanErrorStateChangeEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Reception time
        ("errorState", SilKit_CanErrorState), # CAN controller error state
    ]
SilKit_CanErrorStateChangeEvent_p = ctypes.POINTER(SilKit_CanErrorStateChangeEvent)

class SilKit_CanController(ctypes.Structure):
    _pack_ = 8
SilKit_CanController_p = ctypes.POINTER(SilKit_CanController)

SilKit_CanFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_CanController_p,
    SilKit_CanFrameTransmitEvent_p
)

SilKit_CanFrameHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_CanController_p,
    SilKit_CanFrameEvent_p
)

SilKit_CanStateChangeHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_CanController_p,
    SilKit_CanStateChangeEvent_p
)

SilKit_CanErrorStateChangeHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_CanController_p,
    SilKit_CanErrorStateChangeEvent_p
)

# The lifetime of the resulting CAN controller is directly bound to the lifetime of the simulation participant.
# The object returned must not be deallocated using free()
SilKit_CanController_Create = _silkit_.SilKit_CanController_Create
SilKit_CanController_Create.restype = SilKit_ReturnCode
SilKit_CanController_Create.argtypes = [
    ctypes.POINTER(SilKit_CanController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
]
SilKit_CanController_Create.errcheck = check_silkit_status
SilKit_CanController_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_CanController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
)

SilKit_CanController_Start = _silkit_.SilKit_CanController_Start
SilKit_CanController_Start.restype = SilKit_ReturnCode
SilKit_CanController_Start.argtypes = [
    SilKit_CanController_p
]
SilKit_CanController_Start.errcheck = check_silkit_status
SilKit_CanController_Start_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p
)

SilKit_CanController_Stop = _silkit_.SilKit_CanController_Stop
SilKit_CanController_Stop.restype = SilKit_ReturnCode
SilKit_CanController_Stop.argtypes = [
    SilKit_CanController_p
]
SilKit_CanController_Stop.errcheck = check_silkit_status
SilKit_CanController_Stop_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p
)

SilKit_CanController_Reset = _silkit_.SilKit_CanController_Reset
SilKit_CanController_Reset.restype = SilKit_ReturnCode
SilKit_CanController_Reset.argtypes = [
    SilKit_CanController_p
]
SilKit_CanController_Reset.errcheck = check_silkit_status
SilKit_CanController_Reset_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p
)

SilKit_CanController_Sleep = _silkit_.SilKit_CanController_Sleep
SilKit_CanController_Sleep.restype = SilKit_ReturnCode
SilKit_CanController_Sleep.argtypes = [
    SilKit_CanController_p
]
SilKit_CanController_Sleep.errcheck = check_silkit_status
SilKit_CanController_Sleep_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p
)

SilKit_CanController_SendFrame = _silkit_.SilKit_CanController_SendFrame
SilKit_CanController_SendFrame.restype = SilKit_ReturnCode
SilKit_CanController_SendFrame.argtypes = [
    SilKit_CanController_p,
    SilKit_CanFrame_p,
    ctypes.c_void_p
]
SilKit_CanController_SendFrame.errcheck = check_silkit_status
SilKit_CanController_SendFrame_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    SilKit_CanFrame_p,
    ctypes.c_void_p
)

SilKit_CanController_SetBaudRate = _silkit_.SilKit_CanController_SetBaudRate
SilKit_CanController_SetBaudRate.restype = SilKit_ReturnCode
SilKit_CanController_SetBaudRate.argtypes = [
    SilKit_CanController_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32
]
SilKit_CanController_SetBaudRate.errcheck = check_silkit_status
SilKit_CanController_SetBaudRate_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32
)

# Full support in a detailed simulation. In simple simulation, all messages are automatically positively acknowledged.
SilKit_CanController_AddFrameTransmitHandler = _silkit_.SilKit_CanController_AddFrameTransmitHandler
SilKit_CanController_AddFrameTransmitHandler.restype = SilKit_ReturnCode
SilKit_CanController_AddFrameTransmitHandler.argtypes = [
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanFrameTransmitHandler_t,
    SilKit_CanTransmitStatus,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_CanController_AddFrameTransmitHandler.errcheck = check_silkit_status
SilKit_CanController_AddFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanFrameTransmitHandler_t,
    SilKit_CanTransmitStatus,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_CanController_RemoveFrameTransmitHandler = _silkit_.SilKit_CanController_RemoveFrameTransmitHandler
SilKit_CanController_RemoveFrameTransmitHandler.restype = SilKit_ReturnCode
SilKit_CanController_RemoveFrameTransmitHandler.argtypes = [
    SilKit_CanController_p,
    SilKit_HandlerId
]
SilKit_CanController_RemoveFrameTransmitHandler.errcheck = check_silkit_status
SilKit_CanController_RemoveFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    SilKit_HandlerId
)

SilKit_CanController_AddFrameHandler = _silkit_.SilKit_CanController_AddFrameHandler
SilKit_CanController_AddFrameHandler.restype = SilKit_ReturnCode
SilKit_CanController_AddFrameHandler.argtypes = [
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanFrameHandler_t,
    SilKit_Direction,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_CanController_AddFrameHandler.errcheck = check_silkit_status
SilKit_CanController_AddFrameHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanFrameHandler_t,
    SilKit_Direction,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_CanController_RemoveFrameHandler = _silkit_.SilKit_CanController_RemoveFrameHandler
SilKit_CanController_RemoveFrameHandler.restype = SilKit_ReturnCode
SilKit_CanController_RemoveFrameHandler.argtypes = [
    SilKit_CanController_p,
    SilKit_HandlerId
]
SilKit_CanController_RemoveFrameHandler.errcheck = check_silkit_status
SilKit_CanController_RemoveFrameHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    SilKit_HandlerId
)

SilKit_CanController_AddStateChangeHandler = _silkit_.SilKit_CanController_AddStateChangeHandler
SilKit_CanController_AddStateChangeHandler.restype = SilKit_ReturnCode
SilKit_CanController_AddStateChangeHandler.argtypes = [
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanStateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_CanController_AddStateChangeHandler.errcheck = check_silkit_status
SilKit_CanController_AddStateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanStateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_CanController_RemoveStateChangeHandler = _silkit_.SilKit_CanController_RemoveStateChangeHandler
SilKit_CanController_RemoveStateChangeHandler.restype = SilKit_ReturnCode
SilKit_CanController_RemoveStateChangeHandler.argtypes = [
    SilKit_CanController_p,
    SilKit_HandlerId
]
SilKit_CanController_RemoveStateChangeHandler.errcheck = check_silkit_status
SilKit_CanController_RemoveStateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    SilKit_HandlerId
)

SilKit_CanController_AddErrorStateChangeHandler = _silkit_.SilKit_CanController_AddErrorStateChangeHandler
SilKit_CanController_AddErrorStateChangeHandler.restype = SilKit_ReturnCode
SilKit_CanController_AddErrorStateChangeHandler.argtypes = [
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanErrorStateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_CanController_AddErrorStateChangeHandler.errcheck = check_silkit_status
SilKit_CanController_AddErrorStateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    ctypes.c_void_p,
    SilKit_CanErrorStateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_CanController_RemoveErrorStateChangeHandler = _silkit_.SilKit_CanController_RemoveErrorStateChangeHandler
SilKit_CanController_RemoveErrorStateChangeHandler.restype = SilKit_ReturnCode
SilKit_CanController_RemoveErrorStateChangeHandler.argtypes = [
    SilKit_CanController_p,
    SilKit_HandlerId
]
SilKit_CanController_RemoveErrorStateChangeHandler.errcheck = check_silkit_status
SilKit_CanController_RemoveErrorStateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_CanController_p,
    SilKit_HandlerId
)

###### Ethernet.h ######

SilKit_EthernetTransmitStatus = ctypes.c_uint32
class SilKitEthernetTransmitStatus(enum.IntEnum):
    # The message was successfully transmitted on the CAN bus.
    TRANSMITTED = BIT(0)
    # The transmit request was rejected, because the Ethernet controller is not active.
    CONTROLLER_INACTIVE = BIT(1)
    # The transmit request was rejected, because the Ethernet link is down.
    LINK_DOWN = BIT(2)
    # The transmit request was dropped, because the transmit queue is full.
    DROPPED = BIT(3)
    # BIT(4) is RESERVED (used to be DUPLICATED_TRANSMIT_ID)
    # The given raw Ethernet frame is ill formated (e.g. frame length is too small or too large, etc.).
    INVALID_FRAME_FORMAT = BIT(5)
    # Combines all available transmit statuses.
    Default_Mask = TRANSMITTED | CONTROLLER_INACTIVE | LINK_DOWN | DROPPED | INVALID_FRAME_FORMAT

SilKit_EthernetState = ctypes.c_uint32
class SilKitEthernetState(enum.IntEnum):
    # The Ethernet controller is switched off (default after reset).
    INACTIVE = 0
    # The Ethernet controller is active, but a link to another Ethernet controller in not yet established.
    LINK_DOWN = 1
    # The Ethernet controller is active and the link to another Ethernet controller is established.
    LINK_UP = 2

class SilKit_EthernetStateChangeEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id that specifies which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Timestamp of the state change event
        ("state", SilKit_EthernetState), # New state of the Ethernet controller
    ]

SilKit_EthernetBitrate = ctypes.c_uint32 # Bitrate in kBit/sec
class SilKit_EthernetBitrateChangeEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id that specifies which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Timestamp of the bitrate change event
        ("bitrate", SilKit_EthernetBitrate), # New bitrate in kBit/sec
    ]

# A raw Ethernet frame
class SilKit_EthernetFrame(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id that specifies which version of this struct was obtained
        ("raw", SilKit_ByteVector)
    ]

class SilKit_EthernetFrameEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id that specifies which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Send time
        ("ethernetFrame", ctypes.POINTER(SilKit_EthernetFrame)), # The raw Ethernet frame
        ("direction", SilKit_Direction), # Receive/Transmit direction
        ("userContext", ctypes.c_void_p), # Optional pointer provided by user when sending the frame
    ]

class SilKit_EthernetFrameTransmitEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id that specifies which version of this struct was obtained
        ("userContext", ctypes.c_void_p), # Value that was provided by user in corresponding parameter on send of Ethernet frame
        ("timestamp", SilKit_NanosecondsTime), # Reception time
        ("status", SilKit_EthernetTransmitStatus), # Status of the EthernetTransmitRequest
    ]

class SilKit_EthernetController(ctypes.Structure):
    _pack_ = 8
SilKit_EthernetController_p = ctypes.POINTER(SilKit_EthernetController)

SilKit_EthernetFrameHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_EthernetController_p,
    ctypes.POINTER(SilKit_EthernetFrameEvent)
)

SilKit_EthernetFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p,
    SilKit_EthernetController_p,
    ctypes.POINTER(SilKit_EthernetFrameTransmitEvent)
)

SilKit_EthernetStateChangeHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_EthernetController_p,
    ctypes.POINTER(SilKit_EthernetStateChangeEvent)
)

SilKit_EthernetBitrateChangeHandler_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p,
    SilKit_EthernetController_p,
    ctypes.POINTER(SilKit_EthernetBitrateChangeEvent)
)

SilKit_EthernetController_Create = _silkit_.SilKit_EthernetController_Create
SilKit_EthernetController_Create.restype = SilKit_ReturnCode
SilKit_EthernetController_Create.argtypes = [
    ctypes.POINTER(SilKit_EthernetController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
]
SilKit_EthernetController_Create.errcheck = check_silkit_status
SilKit_EthernetController_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_EthernetController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
)

SilKit_EthernetController_Activate = _silkit_.SilKit_EthernetController_Activate
SilKit_EthernetController_Activate.restype = SilKit_ReturnCode
SilKit_EthernetController_Activate.argtypes = [
    SilKit_EthernetController_p
]
SilKit_EthernetController_Activate.errcheck = check_silkit_status
SilKit_EthernetController_Activate_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p
)

SilKit_EthernetController_Deactivate = _silkit_.SilKit_EthernetController_Deactivate
SilKit_EthernetController_Deactivate.restype = SilKit_ReturnCode
SilKit_EthernetController_Deactivate.argtypes = [
    SilKit_EthernetController_p
]
SilKit_EthernetController_Deactivate.errcheck = check_silkit_status
SilKit_EthernetController_Deactivate_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p
)

SilKit_EthernetController_AddFrameHandler = _silkit_.SilKit_EthernetController_AddFrameHandler
SilKit_EthernetController_AddFrameHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_AddFrameHandler.argtypes = [
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetFrameHandler_t,
    SilKit_Direction,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_EthernetController_AddFrameHandler.errcheck = check_silkit_status
SilKit_EthernetController_AddFrameHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetFrameHandler_t,
    SilKit_Direction,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_EthernetController_RemoveFrameHandler = _silkit_.SilKit_EthernetController_RemoveFrameHandler
SilKit_EthernetController_RemoveFrameHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_RemoveFrameHandler.argtypes = [
    SilKit_EthernetController_p,
    SilKit_HandlerId
]
SilKit_EthernetController_RemoveFrameHandler.errcheck = check_silkit_status
SilKit_EthernetController_RemoveFrameHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    SilKit_HandlerId
)

SilKit_EthernetController_AddFrameTransmitHandler = _silkit_.SilKit_EthernetController_AddFrameTransmitHandler
SilKit_EthernetController_AddFrameTransmitHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_AddFrameTransmitHandler.argtypes = [
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetFrameTransmitHandler_t,
    SilKit_EthernetTransmitStatus,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_EthernetController_AddFrameTransmitHandler.errcheck = check_silkit_status
SilKit_EthernetController_AddFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetFrameTransmitHandler_t,
    SilKit_EthernetTransmitStatus,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_EthernetController_RemoveFrameTransmitHandler = _silkit_.SilKit_EthernetController_RemoveFrameTransmitHandler
SilKit_EthernetController_RemoveFrameTransmitHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_RemoveFrameTransmitHandler.argtypes = [
    SilKit_EthernetController_p,
    SilKit_HandlerId
]
SilKit_EthernetController_RemoveFrameTransmitHandler.errcheck = check_silkit_status
SilKit_EthernetController_RemoveFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    SilKit_HandlerId
)

SilKit_EthernetController_AddStateChangeHandler = _silkit_.SilKit_EthernetController_AddStateChangeHandler
SilKit_EthernetController_AddStateChangeHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_AddStateChangeHandler.argtypes = [
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetStateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_EthernetController_AddStateChangeHandler.errcheck = check_silkit_status
SilKit_EthernetController_AddStateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetStateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)


SilKit_EthernetController_RemoveStateChangeHandler = _silkit_.SilKit_EthernetController_RemoveStateChangeHandler
SilKit_EthernetController_RemoveStateChangeHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_RemoveStateChangeHandler.argtypes = [
    SilKit_EthernetController_p,
    SilKit_HandlerId
]
SilKit_EthernetController_RemoveStateChangeHandler.errcheck = check_silkit_status
SilKit_EthernetController_RemoveStateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    SilKit_HandlerId
)

SilKit_EthernetController_AddBitrateChangeHandler = _silkit_.SilKit_EthernetController_AddBitrateChangeHandler
SilKit_EthernetController_AddBitrateChangeHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_AddBitrateChangeHandler.argtypes = [
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetBitrateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_EthernetController_AddBitrateChangeHandler.errcheck = check_silkit_status
SilKit_EthernetController_AddBitrateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    ctypes.c_void_p,
    SilKit_EthernetBitrateChangeHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_EthernetController_RemoveBitrateChangeHandler = _silkit_.SilKit_EthernetController_RemoveBitrateChangeHandler
SilKit_EthernetController_RemoveBitrateChangeHandler.restype = SilKit_ReturnCode
SilKit_EthernetController_RemoveBitrateChangeHandler.argtypes = [
    SilKit_EthernetController_p,
    SilKit_HandlerId
]
SilKit_EthernetController_RemoveBitrateChangeHandler.errcheck = check_silkit_status
SilKit_EthernetController_RemoveBitrateChangeHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    SilKit_HandlerId
)

SilKit_EthernetController_SendFrame = _silkit_.SilKit_EthernetController_SendFrame
SilKit_EthernetController_SendFrame.restype = SilKit_ReturnCode
SilKit_EthernetController_SendFrame.argtypes = [
    SilKit_EthernetController_p,
    ctypes.POINTER(SilKit_EthernetFrame),
    ctypes.c_void_p
]
SilKit_EthernetController_SendFrame.errcheck = check_silkit_status
SilKit_EthernetController_SendFrame_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_EthernetController_p,
    ctypes.POINTER(SilKit_EthernetFrame),
    ctypes.c_void_p
)

###### Flexray.h ######

# FlexRay micro tick
SilKit_FlexrayMicroTick = ctypes.c_int32
# FlexRay macro tick
SilKit_FlexrayMacroTick = ctypes.c_int32

SilKit_FlexrayChannel = ctypes.c_uint32
class SilKitFlexrayChannel(enum.IntEnum):
    NONE = 0x00
    A = 0x01
    B = 0x02
    AB = A | B # 3

#Period of the clock (used for micro tick period and sample clock period).
SilKit_FlexrayClockPeriod = ctypes.c_uint32
class SilKitFlexrayClockPeriod(enum.IntEnum):
    T12_5NS = 1 # 12.5ns / 80MHz
    T25NS = 2 # 25ns   / 40MHz
    T50NS = 3 # 50ns   / 20MHz

class SilKit_FlexrayClusterParameters(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        # Number of attempts for a cold start before giving up (range 2-31).
        ("gColdstartAttempts", ctypes.c_ubyte),
        # Max cycle count value in a given cluster (range 7-63, must be an odd integer).
        ("gCycleCountMax", ctypes.c_ubyte),
        # Time offset for a static slot in MacroTicks (MT) (range 1-63).
        ("gdActionPointOffset", ctypes.c_uint16),
        # gdCASRxLowMax # Not used by network simulator
        # Duration of the idle phase within a dynamic slot in gdMiniSlots (range 0-2).
        ("gdDynamicSlotIdlePhase", ctypes.c_uint16),
        # gdIgnoreAfterTx # Not used by network simulator
        # Duration of a mini slot in MacroTicks (MT) (2-63).
        ("gdMiniSlot", ctypes.c_uint16),
        # Time offset for a mini slot in MacroTicks (MT) (range 1-31).
        ("gdMiniSlotActionPointOffset", ctypes.c_uint16),
        # Duration of a static slot in MacroTicks (MT) (3-664).
        ("gdStaticSlot", ctypes.c_uint16),
        # Duration of the symbol window in MacroTicks (MT) (range 0-162).
        ("gdSymbolWindow", ctypes.c_uint16),
        # Time offset for a static symbol windows in MacroTicks (MT) (range 1-63).
        ("gdSymbolWindowActionPointOffset", ctypes.c_uint16),
        # Duration of TSS (Transmission Start Sequence) in gdBits (range 1-15).
        ("gdTSSTransmitter", ctypes.c_uint16),
        # gdWakeupRxIdle # Not used by network simulator
        # gdWakeupRxLow # Not used by network simulator
        # gdWakeupRxWindow # Not used by network simulator
        # Duration of LOW Phase of a wakeup symbol in gdBit (range 15-60).
        ("gdWakeupTxActive", ctypes.c_uint16),
        # Duration of the idle of a wakeup symbol in gdBit (45-180).
        ("gdWakeupTxIdle", ctypes.c_uint16),
        # Upper limit for the startup listen timeout and wakeup listen timeout in the
        # presence of noise. Used as a multiplier of pdListenTimeout (range 2-16).
        ("gListenNoise", ctypes.c_ubyte),
        # Number of MacroTicks (MT) per cycle, (range 8-16000).
        ("gMacroPerCycle", ctypes.c_uint16),
        # Threshold used for testing the vClockCorrectionFailed counter (range 1-15).
        ("gMaxWithoutClockCorrectionFatal", ctypes.c_ubyte),
        # Threshold used for testing the vClockCorrectionFailed counter (range 1-15).
        ("gMaxWithoutClockCorrectionPassive", ctypes.c_ubyte),
        # Number of mini slots (range 0-7988).
        ("gNumberOfMiniSlots", ctypes.c_uint16),
        # Number of static slots in a cycle (range 2-1023).
        ("gNumberOfStaticSlots", ctypes.c_uint16),
        # Length of the payload of a static frame in 16-Bits words (range 0-127).
        ("gPayloadLengthStatic", ctypes.c_uint16),
        # Max number of distinct sync frame identifiers present in a given cluster. (range 2-15).
        ("gSyncFrameIDCountMax", ctypes.c_ubyte)
    ]

class  SilKit_FlexrayNodeParameters(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        # Parameters according to B.3.2.1
        # Controls the transition to halt state due to clock synchronization errors. (0,1).
        ("pAllowHaltDueToClock", ctypes.c_ubyte),
        # Required number of consecutive even / odd cycle pairs for normal passive to normal active (range 0-31).
        ("pAllowPassiveToActive", ctypes.c_ubyte),
        # Channel(s) to which the controller is connected (values FlexrayChannel::A, FlexrayChannel::B, FlexrayChannel::AB).
        ("pChannels", SilKit_FlexrayChannel),
        # Cluster drift damping factor for rate correction in MicroTicks (range 0-10).
        ("pClusterDriftDamping", ctypes.c_ubyte),
        # Allowed deviation for startup frames during integration in MicroTicks (range 29-2743).
        ("pdAcceptedStartupRange", SilKit_FlexrayMicroTick),
        # pDecodingCorrection # Not used by network simulator
        # pDelayCompensationA # Not used by network simulator
        # pDelayCompensationB # Not used by network simulator
        # Duration of listen phase in MicroTicks (range 1926-2567692).
        ("pdListenTimeout", SilKit_FlexrayMicroTick),
        # pExternalSync # Not used by network simulator
        # pExternOffsetCorrection # Not used by network simulator
        # pExternRateCorrection # Not used by network simulator
        # pFallBackInternal # Not used by network simulator
        # Slot ID of the key slot (range 0-1023, value 0 means that there is no key slot).
        ("pKeySlotId", ctypes.c_uint16),
        # Shall the node enter key slot only mode after startup. (values 0, 1) (AUTOSAR pSingleSlotEnabled).
        ("pKeySlotOnlyEnabled", ctypes.c_ubyte),
        # Key slot is used for startup (range 0, 1).
        ("pKeySlotUsedForStartup", ctypes.c_ubyte),
        # Key slot is used for sync (range 0, 1).
        ("pKeySlotUsedForSync", ctypes.c_ubyte),
        # Last mini slot which can be transmitted (range 0-7988).
        ("pLatestTx", ctypes.c_uint16),
        # Initial startup offset for frame reference point on channel A (rang 2-68 MacroTicks (MT)).
        ("pMacroInitialOffsetA", ctypes.c_ubyte),
        # Initial startup offset for frame reference point on channel B (rang 2-68 MacroTicks (MT)).
        ("pMacroInitialOffsetB", ctypes.c_ubyte),
        # Offset between secondary time reference and MT boundary (range 0-239 MicroTicks).
        ("pMicroInitialOffsetA", SilKit_FlexrayMicroTick),
        # Offset between secondary time reference and MT boundary (range 0-239 MicroTicks).
        ("pMicroInitialOffsetB", SilKit_FlexrayMicroTick),
        # Nominal number of MicroTicks in the communication cycle (range 960-1280000).
        ("pMicroPerCycle", SilKit_FlexrayMicroTick),
        # Maximum permissible offset correction value (range 15-16082 MicroTicks).
        ("pOffsetCorrectionOut", SilKit_FlexrayMicroTick),
        # Start of the offset correction phase within the NIT, (7-15999 MT).
        ("pOffsetCorrectionStart", ctypes.c_uint16),
        # Maximum permissible rate correction value (range 3-3846 MicroTicks).
        ("pRateCorrectionOut", SilKit_FlexrayMicroTick),
        # pSecondKeySlotID # Not used by network simulator
        # pTwoKeySlotMode # Not used by network simulator
        # Channel used by the node to send a wakeup pattern (values FlexrayChannel::A, FlexrayChannel::B).
        ("pWakeupChannel", SilKit_FlexrayChannel),
        # Number of repetitions of the wakeup symbol (range 0-63, value 0 or 1 prevents sending of WUP).
        ("pWakeupPattern", ctypes.c_ubyte),
        # Parameters according to B.3.2.2
        # Duration of a FlexRay MicroTick (12.5ns, 25ns or 50ns).
        ("pdMicrotick", SilKit_FlexrayClockPeriod),
        # pNMVectorEarlyUpdate # Not used by network simulator
        # pPayloadLengthDynMax # Not used by network simulator
        # Number of samples per MicroTick (values 1 or 2).
        ("pSamplesPerMicrotick", ctypes.c_ubyte)
    ]

# Transmission mode for FlexRay Tx-Buffer
SilKit_FlexrayTransmissionMode = ctypes.c_ubyte
class SilKitFlexrayTransmissionMode(enum.IntEnum):
    SINGLE_SHOT = 0
    CONTINUOUS = 1

# Configuration of Tx-Buffer, used in struct FlexrayControllerConfig
class  SilKit_FlexrayTxBufferConfig(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        ("channels", SilKit_FlexrayChannel), # SilKitFlexrayChannel.A | B
        ("slotId", ctypes.c_uint16), # The slot Id of frame
        ("offset", ctypes.c_ubyte), # Base offset for cycle multiplexing (values 0-63)
        ("repetition", ctypes.c_ubyte), # Repetition for cycle multiplexing (values 1,2,4,8,16,32,64)
        ("hasPayloadPreambleIndicator", SilKit_Bool), # Set the PPindicator
        ("headerCrc", ctypes.c_uint16), # Header CRC, 11 bits
        ("transmissionMode", SilKit_FlexrayTransmissionMode), # SilKitFlexrayTransmissionMode.SINGLE_SHOT | CONTINUOUS
    ]

# Configure the communication parameters of the FlexRay controller.
class  SilKit_FlexrayControllerConfig(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        ("clusterParams", ctypes.POINTER(SilKit_FlexrayClusterParameters)), # FlexRay cluster parameters
        ("nodeParams", ctypes.POINTER(SilKit_FlexrayNodeParameters)), # FlexRay node parameters
        ("numBufferConfigs", ctypes.c_uint32), # FlexRay buffer configs
        ("bufferConfigs", ctypes.POINTER(SilKit_FlexrayTxBufferConfig))
    ]

# Update the content of a FlexRay TX-Buffer
class  SilKit_FlexrayTxBufferUpdate(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        # Index of the TX Buffers according to the configured buffers (cf. FlexrayControllerConfig).
        ("txBufferIndex", ctypes.c_uint16),
        ("payloadDataValid", SilKit_Bool), # Payload data valid flag
        ("payload", SilKit_ByteVector), # Raw payload containing 0 to 254 bytes.
    ]

# FlexRay controller commands
SilKit_FlexrayChiCommand = ctypes.c_ubyte
class SilKitFlexrayChiCommand(enum.IntEnum):
    RUN = 0x00
    DEFERRED_HALT = 0x01
    FREEZE = 0x02
    ALLOW_COLDSTART = 0x03
    ALL_SLOTS = 0x04
    WAKEUP = 0x05

SilKit_FlexrayHeader_Flag = ctypes.c_ubyte
class SilKitFlexrayHeaderFlag(enum.IntEnum):
    SUF_INDICATOR = 0X01
    SYF_INDICATOR = 0X02
    NF_INDICATOR = 0X04
    PP_INDICATOR = 0X08

class  SilKit_FlexrayHeader(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        #[7-5]: unused
        #[4]: Reserved bit
        #[3]: PPIndicator: 0, regular payload; 1, NM vector or message ID
        #[2]: NFIndicator: 0, no valid payload data and PPIndicator = 0; 1, valid payload data
        #[1]: SyFIndicator: 0, frame not used for synchronization; 1, frame shall be used for sync
        #[0]: SuFIndicator: 0, not a startup frame; 1, a startup frame
        ("flags", ctypes.c_ubyte),
        ("frameId", ctypes.c_uint16), # Slot ID in which the frame was sent: 1 - 2047
        ("payloadLength", ctypes.c_ubyte), # Payload length, 7 bits
        ("headerCrc", ctypes.c_uint16), # Header CRC, 11 bits
        ("cycleCount", ctypes.c_ubyte), # Cycle in which the frame was sent: 0 - 63
    ]

class  SilKit_FlexrayFrame(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("header", ctypes.POINTER(SilKit_FlexrayHeader)), # Header flags, slot, crc, and cycle indidcators
        ("payload", SilKit_ByteVector)
    ]

class  SilKit_FlexrayFrameEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time at end of frame transmission
        ("channel", SilKit_FlexrayChannel), # FlexRay channel A or B. (Valid values: FlexrayChannel::A, FlexrayChannel::B).
        ("frame", ctypes.POINTER(SilKit_FlexrayFrame)), # Received FlexRay frame
    ]

class  SilKit_FlexrayFrameTransmitEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time at end of frame transmission
        ("txBufferIndex", ctypes.c_uint16), # Tx buffer, that was used for the transmission
        ("channel", SilKit_FlexrayChannel), # FlexRay channel A or B. (Valid values: FlexrayChannel::A, FlexrayChannel::B).
        ("frame", ctypes.POINTER(SilKit_FlexrayFrame)), # Copy of the FlexRay frame that was successfully transmitted
    ]

SilKit_FlexraySymbolPattern = ctypes.c_ubyte
class SilKitFlexraySymbolPattern(enum.IntEnum):
    # Collision avoidance symbol (CAS) OR media access test symbol (MTS).
    CAS_MTS = 0x00
    WUS = 0x01# Wakeup symbol (WUS)
    WUDOP = 0x02# Wakeup During Operation Pattern (WUDOP)

class  SilKit_FlexraySymbolEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # End time of symbol reception.
        ("channel", SilKit_FlexrayChannel), # FlexRay channel A or B (values: FlexrayChannel::A, FlexrayChannel::B).
        ("pattern", SilKit_FlexraySymbolPattern), # The received symbol, e.g. wakeup pattern
    ]
SilKit_FlexraySymbolTransmitEvent = SilKit_FlexraySymbolEvent
SilKit_FlexrayWakeupEvent = SilKit_FlexraySymbolEvent

class  SilKit_FlexrayCycleStartEvent(ctypes.Structure):
    ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
    ("timestamp", SilKit_NanosecondsTime), # Cycle starting time.
    ("cycleCounter", ctypes.c_ubyte), # Counter of FlexRay cycles.

#Protocol Operation Control (POC) state of the FlexRay communication controller
SilKit_FlexrayPocState = ctypes.c_ubyte
class SilKitFlexrayPocState(enum.IntEnum):
    # CC expects configuration. Initial state after reset.
    DEFAULT_CONFIG = 0x00
    # CC is in configuration mode for setting communication parameters
    CONFIG = 0x01
    READY = 0x02 # intermediate state for initialization process (after Config)
    STARTUP = 0x03 # FlexRay startup phase
    WAKEUP = 0x04 # FlexRay wakeup phase
    NORMAL_ACTIVE = 0x05 # Normal operating mode
    NORMAL_PASSIVE = 0x06 # Operating mode with transient or tolerable errors
    # CC is halted (caused by the application (FlexrayChiCommand.DEFERRED_HALT) or by a fatal error).
    HALT = 0x07

SilKit_FlexraySlotModeType = ctypes.c_ubyte
class SilKitFlexraySlotModeType(enum.IntEnum):
    KEYSLOT = 0x00
    ALL_PENDING = 0x01
    ALL = 0x02

SilKit_FlexrayErrorModeType = ctypes.c_ubyte
class SilKitFlexrayErrorModeType(enum.IntEnum):
    ACTIVE = 0X00
    PASSIVE = 0X01
    COMM_HALT = 0X02

SilKit_FlexrayStartupStateType = ctypes.c_ubyte
class SilKitFlexrayStartupStateType(enum.IntEnum):
    UNDEFINED = 0X00
    COLDSTART_LISTEN = 0X01
    INTEGRATION_COLDSTART_CHECK = 0X02
    COLDSTART_JOIN = 0X03
    COLDSTART_COLLISION_RESOLUTION = 0X04
    COLDSTART_CONSISTENCY_CHECK = 0X05
    INTEGRATION_LISTEN = 0X06
    INITIALIZE_SCHEDULE = 0X07
    INTEGRATION_CONSISTENCY_CHECK = 0X08
    COLDSTART_GAP = 0X09
    EXTERNAL_STARTUP = 0X0A

SilKit_FlexrayWakeupStatusType = ctypes.c_ubyte
class SilKitFlexrayWakeupStatusType(enum.IntEnum):
    UNDEFINED = 0X00
    RECEIVED_HEADER = 0X01
    RECEIVED_WUP = 0X02
    COLLISION_HEADER = 0X03
    COLLISION_WUP = 0X04
    COLLISION_UNKNOWN = 0X05
    TRANSMITTED = 0X06

# This enhances the deprecated struct ControllerStatus by adding  members
# that are available through the Controller Host Interface.
class  SilKit_FlexrayPocStatusEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # SIL Kit timestamp
        # Status of the Protocol Operation Control (POC).
        ("state", SilKit_FlexrayPocState),
        ("chiHaltRequest", SilKit_Bool), # indicates whether a halt request was received from the CHI
        ("coldstartNoise", SilKit_Bool), # indicates noisy channel conditions during coldstart
        # indicates that the POC entered a halt state due to an error condition requiring immediate halt.
        ("freeze", SilKit_Bool),
        # indicates that the CHI requested to enter ready state at the end of the communication cycle.
        ("chiReadyRequest", SilKit_Bool),
        # indicates the error mode of the POC
        ("errorMode", SilKit_FlexrayErrorModeType),
        # indicates the slot mode of the POC
        ("slotMode", SilKit_FlexraySlotModeType),
        # indicates states within the STARTUP mechanism
        ("startupState", SilKit_FlexrayStartupStateType),
        # outcome of the execution of the WAKEUP mechanism
        ("wakeupStatus", SilKit_FlexrayWakeupStatusType)
    ]

# class SilKit_FlexrayController(ctypes.Structure):
#     _pack_ = 8
SilKit_FlexrayController_p = ctypes.c_void_p

SilKit_FlexrayFrameHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayFrameEvent)
)

SilKit_FlexrayFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayFrameTransmitEvent)
)

SilKit_FlexrayWakeupHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayWakeupEvent)
)

SilKit_FlexrayPocStatusHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayPocStatusEvent)
)

SilKit_FlexraySymbolHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexraySymbolEvent)
)

SilKit_FlexraySymbolTransmitHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexraySymbolTransmitEvent)
)

SilKit_FlexrayCycleStartHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayCycleStartEvent)
)

# The object returned must not be deallocated using free()!
SilKit_FlexrayController_Create = _silkit_.SilKit_FlexrayController_Create
SilKit_FlexrayController_Create.restype = SilKit_ReturnCode
SilKit_FlexrayController_Create.argtypes = [
    ctypes.POINTER(SilKit_FlexrayController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
]
SilKit_FlexrayController_Create.errcheck = check_silkit_status
SilKit_FlexrayController_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_FlexrayController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
)

#Apply the given controller configuration to the controller.
SilKit_FlexrayController_Configure = _silkit_.SilKit_FlexrayController_Configure
SilKit_FlexrayController_Configure.restype = SilKit_ReturnCode
SilKit_FlexrayController_Configure.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayControllerConfig)
]
SilKit_FlexrayController_Configure.errcheck = check_silkit_status
SilKit_FlexrayController_Configure_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayControllerConfig)
)

#Reconfigure a TX Buffer that was previously setup with SilKit_FlexrayController_Configure()
SilKit_FlexrayController_ReconfigureTxBuffer = _silkit_.SilKit_FlexrayController_ReconfigureTxBuffer
SilKit_FlexrayController_ReconfigureTxBuffer.restype = SilKit_ReturnCode
SilKit_FlexrayController_ReconfigureTxBuffer.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_uint16,
    ctypes.POINTER(SilKit_FlexrayTxBufferConfig)
]
SilKit_FlexrayController_ReconfigureTxBuffer.errcheck = check_silkit_status
SilKit_FlexrayController_ReconfigureTxBuffer_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_uint16,
    ctypes.POINTER(SilKit_FlexrayTxBufferConfig)
)

# Update the content of a previously configured TX buffer.
# A FlexRay message will be sent at the time matching the configured Slot ID. 
# If the buffer was configured with FlexrayTransmissionMode::SingleShot,
# the content is sent exactly once. If it is configured as FlexrayTransmissionMode::Continuous,
# the content is sent repeatedly according to the offset and repetition configuration.
SilKit_FlexrayController_UpdateTxBuffer = _silkit_.SilKit_FlexrayController_UpdateTxBuffer
SilKit_FlexrayController_UpdateTxBuffer.restype = SilKit_ReturnCode
SilKit_FlexrayController_UpdateTxBuffer.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayTxBufferUpdate)
]
SilKit_FlexrayController_UpdateTxBuffer.errcheck = check_silkit_status
SilKit_FlexrayController_UpdateTxBuffer_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.POINTER(SilKit_FlexrayTxBufferUpdate)
)

# Send the given FlexrayChiCommand.
SilKit_FlexrayController_ExecuteCmd = _silkit_.SilKit_FlexrayController_ExecuteCmd
SilKit_FlexrayController_ExecuteCmd.restype = SilKit_ReturnCode
SilKit_FlexrayController_ExecuteCmd.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_FlexrayChiCommand
]
SilKit_FlexrayController_ExecuteCmd.errcheck = check_silkit_status
SilKit_FlexrayController_ExecuteCmd_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_FlexrayChiCommand
)

SilKit_FlexrayController_AddFrameHandler = _silkit_.SilKit_FlexrayController_AddFrameHandler
SilKit_FlexrayController_AddFrameHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddFrameHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayFrameHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddFrameHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddFrameHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayFrameHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemoveFrameHandler = _silkit_.SilKit_FlexrayController_RemoveFrameHandler
SilKit_FlexrayController_RemoveFrameHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemoveFrameHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemoveFrameHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemoveFrameHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

SilKit_FlexrayController_AddFrameTransmitHandler = _silkit_.SilKit_FlexrayController_AddFrameTransmitHandler
SilKit_FlexrayController_AddFrameTransmitHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddFrameTransmitHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayFrameTransmitHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddFrameTransmitHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayFrameTransmitHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemoveFrameTransmitHandler = _silkit_.SilKit_FlexrayController_RemoveFrameTransmitHandler
SilKit_FlexrayController_RemoveFrameTransmitHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemoveFrameTransmitHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemoveFrameTransmitHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemoveFrameTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

SilKit_FlexrayController_AddWakeupHandler = _silkit_.SilKit_FlexrayController_AddWakeupHandler
SilKit_FlexrayController_AddWakeupHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddWakeupHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayWakeupHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddWakeupHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddWakeupHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayWakeupHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemoveWakeupHandler = _silkit_.SilKit_FlexrayController_RemoveWakeupHandler
SilKit_FlexrayController_RemoveWakeupHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemoveWakeupHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemoveWakeupHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemoveWakeupHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

SilKit_FlexrayController_AddPocStatusHandler = _silkit_.SilKit_FlexrayController_AddPocStatusHandler
SilKit_FlexrayController_AddPocStatusHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddPocStatusHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayPocStatusHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddPocStatusHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddPocStatusHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayPocStatusHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemovePocStatusHandler = _silkit_.SilKit_FlexrayController_RemovePocStatusHandler
SilKit_FlexrayController_RemovePocStatusHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemovePocStatusHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemovePocStatusHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemovePocStatusHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

#The symbols relevant for interaction trigger also an additional callback
SilKit_FlexrayController_AddSymbolHandler = _silkit_.SilKit_FlexrayController_AddSymbolHandler
SilKit_FlexrayController_AddSymbolHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddSymbolHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexraySymbolHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddSymbolHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddSymbolHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexraySymbolHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemoveSymbolHandler = _silkit_.SilKit_FlexrayController_RemoveSymbolHandler
SilKit_FlexrayController_RemoveSymbolHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemoveSymbolHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemoveSymbolHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemoveSymbolHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

# Currently, the following SymbolPatterns can occur:
#  - Wakeup() will cause sending the FlexraySymbolPattern.WUS if the bus is idle.
#  - Run() will cause the transmission of FlexraySymbolPattern.CAS_MTS if configured to coldstart the bus.
SilKit_FlexrayController_AddSymbolTransmitHandler = _silkit_.SilKit_FlexrayController_AddSymbolTransmitHandler
SilKit_FlexrayController_AddSymbolTransmitHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddSymbolTransmitHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexraySymbolTransmitHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddSymbolTransmitHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddSymbolTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexraySymbolTransmitHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemoveSymbolTransmitHandler = _silkit_.SilKit_FlexrayController_RemoveSymbolTransmitHandler
SilKit_FlexrayController_RemoveSymbolTransmitHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemoveSymbolTransmitHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemoveSymbolTransmitHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemoveSymbolTransmitHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

SilKit_FlexrayController_AddCycleStartHandler = _silkit_.SilKit_FlexrayController_AddCycleStartHandler
SilKit_FlexrayController_AddCycleStartHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_AddCycleStartHandler.argtypes = [
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayCycleStartHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_FlexrayController_AddCycleStartHandler.errcheck = check_silkit_status
SilKit_FlexrayController_AddCycleStartHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    ctypes.c_void_p,
    SilKit_FlexrayCycleStartHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_FlexrayController_RemoveCycleStartHandler = _silkit_.SilKit_FlexrayController_RemoveCycleStartHandler
SilKit_FlexrayController_RemoveCycleStartHandler.restype = SilKit_ReturnCode
SilKit_FlexrayController_RemoveCycleStartHandler.argtypes = [
    SilKit_FlexrayController_p,
    SilKit_HandlerId
]
SilKit_FlexrayController_RemoveCycleStartHandler.errcheck = check_silkit_status
SilKit_FlexrayController_RemoveCycleStartHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_FlexrayController_p,
    SilKit_HandlerId
)

###### Lin.h ######

# The operational state of the controller, i.e., operational or sleeping. 
SilKit_LinControllerStatus = ctypes.c_uint32
class SilKitLinControllerStatus(enum.IntEnum):
    UNKNOWN = 0 # The controller state is not yet known.
    OPERATIONAL = 1# Normal operation
    # Sleep state operation; in this state wake-up detection from slave nodes is enabled.
    SLEEP = 2
    # Sleep Pending state is reached when a GoToSleep is issued.
    # This allows the network simulator to finish pending transmissions (e.g., sleep frames to slaves)
    # before entering state Sleep, cf. AUTOSAR SWS LINDriver [SWS_LIN_00266] and section 7.3.3.
    # This is only used when using detailed simulations.
    SLEEP_PENDING = 3

SilKit_LinControllerMode = ctypes.c_ubyte
class SilKitLinControllerMode(enum.IntEnum):
    # The LIN controller has not been configured yet and is inactive.
    INACTIVE = 0
    # A LIN controller with active master task and slave task 
    MASTER = 1
    # A LIN controller with only a slave task 
    SLAVE = 2

SilKit_LinBaudRate = ctypes.c_uint32 # 200...20000 Bd

# Controls the behavior of a LIN Slave task for a particular LIN ID 
SilKit_LinFrameResponseMode = ctypes.c_ubyte
class SilKitLinFrameResponseMode(enum.IntEnum):
    # The LinFrameResponse corresponding to the ID is neither received nor transmitted by the LIN slave. 
    UNUSED = 0
    # The LinFrameResponse corresponding to the ID is received by the LIN slave. 
    RX = 1
    # The LinFrameResponse corresponding to the ID is transmitted unconditionally by the LIN slave. 
    TX_UNCONDITIONAL = 2

SilKit_LinId = ctypes.c_ubyte # 0...0x3F

SilKit_LinChecksumModel = ctypes.c_ubyte
class SilKitLinChecksumModel(enum.IntEnum):
    UNKNOWN = 0 # Unknown checksum model. If configured with this value, the checksum model of the first reception will be used.
    ENHANCED = 1 # Enhanced checksum model
    CLASSIC = 2 # Classic checksum model

SilKit_LinFrameResponseType = ctypes.c_ubyte
class SilKitLinFrameResponseType(enum.IntEnum):
    MASTER_RESPONSE = 0 # Response is generated from this (master) node
    SLAVE_RESPONSE = 1 # Response is generated from a remote slave node
    # Response is generated from one slave to and received by
    # another slave, for the master the response will be anonymous,
    # it does not have to receive the response.
    SLAVE_TO_SLAVE = 2


SilKit_LinFrameStatus = ctypes.c_ubyte
class SilKitLinFrameStatus(enum.IntEnum):
    NOT_OK = 0 # currently not in use
    LIN_TX_OK = 1 # The controller successfully transmitted a frame response.
    LIN_TX_BUSY = 2 # currently not in use
    LIN_TX_HEADER_ERROR = 3 # currently not in use
    LIN_TX_ERROR = 4 # currently not in use
    LIN_RX_OK = 5 # The controller received a correct frame response.
    LIN_RX_BUSY = 6 # currently not in use
    # The reception of a response failed.
    # Indicates a mismatch in expected and received data length or a checksum
    # error. Checksum errors occur when multiple slaves are configured to
    # transmit the same frame or when the sender and receiver use different
    # checksum models.
    LIN_RX_ERROR = 7
    # No LIN controller did provide a response to the frame header. 
    LIN_RX_NO_RESPONSE = 8

SilKit_LinDataLength = ctypes.c_ubyte # 1...8

# If configured for reception with this value, the data length validation of incoming frames is skipped.
SilKit_LinDataLengthUnknown = 255

class SilKit_LinFrame(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("id", SilKit_LinId), # LIN Identifier
        ("checksumModel", SilKit_LinChecksumModel), # Checksum Model
        ("dataLength", SilKit_LinDataLength), # Data length
        ("data", ctypes.c_ubyte * 8) # The actual payload
    ]

# A LIN frame status event delivered in the SilKit_LinFrameStatusHandler_t. 
class SilKit_LinFrameStatusEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time of the event.
        ("frame", ctypes.POINTER(SilKit_LinFrame)),
        ("status", SilKit_LinFrameStatus)
    ]

# A LIN wakeup event delivered in the SilKit_LinWakeupHandler_t. 
class SilKit_LinWakeupEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time of the event.
        ("direction", SilKit_Direction), # The direction of the event.
    ]

# A LIN goToSleep event delivered in the SilKit_LinGoToSleepHandler_t 
class SilKit_LinGoToSleepEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time of the event.
    ]

# A LIN wakeup event delivered in the SilKit_LinWakeupHandler_t. 
class SilKit_Experimental_LinSlaveConfigurationEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time of the event.
    ]

# Configuration data for a LIN Slave task for a particular LIN ID. 
class SilKit_LinFrameResponse(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        # frame must provide the LinId for which the response is configured.
        # If responseMode is TX_UNCONDITIONAL, the frame data is used for the transaction.
        ("frame", ctypes.POINTER(SilKit_LinFrame)),
        # Determines if the LinFrameResponse is used for transmission (TX_UNCONDITIONAL), reception (RX) or ignored (UNUSED).
        ("responseMode", SilKit_LinFrameResponseMode)
    ]

class SilKit_LinControllerConfig(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained 
        ("structHeader", SilKit_StructHeader),
        # Configure as LIN master or LIN slave 
        ("controllerMode", SilKit_LinControllerMode),
        # The operational baud rate of the controller. 
        ("baudRate", SilKit_LinBaudRate),
        ("numFrameResponses", ctypes.c_size_t),
        # LinFrameResponse configuration. 
        ("frameResponses", ctypes.POINTER(SilKit_LinFrameResponse))
    ]

class SilKit_Experimental_LinControllerDynamicConfig(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained 
        ("structHeader", SilKit_StructHeader),
        # Configure as LIN master or LIN slave 
        ("controllerMode", SilKit_LinControllerMode),
        # The operational baud rate of the controller. 
        ("baudRate", SilKit_LinBaudRate)
    ]

class SilKit_Experimental_LinSlaveConfiguration(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained 
        ("structHeader", SilKit_StructHeader),
        # An array of SilKit_LinId on which any LIN Slave has configured TX_UNCONDITIONAL
        ("isLinIdResponding", SilKit_Bool * 64)
    ]

# A LIN frame header event delivered in the SilKit_Experimental_LinFrameHeaderHandler_t. 
class SilKit_Experimental_LinFrameHeaderEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time of the event.
        ("id", SilKit_LinId) # LIN Identifier
    ]

class SilKit_LinSendFrameHeaderRequest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime), # Time of the event.
        ("id", SilKit_LinId) # LIN Identifier
    ]


 # The LIN controller can assume the role of a LIN master or a LIN
 # slave. It provides two kinds of interfaces to perform data
 # transfers and provide frame responses:
 # AUTOSAR-like LIN master interface:
 # - SilKit_LinController_SendFrame() transfers a frame from or to a LIN
 # master. Requires SilKit_LinControllerMode_Master.
 # non-AUTOSAR interface:
 # - SilKit_LinController_SendFrameHeader() initiates the transmission of a
 # LIN frame for a particular LIN identifier. For a successful
 # transmission, exactly one LIN slave or master must have previously
 # set a corresponding frame response for unconditional
 # transmission. Requires SilKit_LinControllerMode_Master.

class SilKit_LinController(ctypes.Structure):
    _pack_ = 8
SilKit_LinController_p = ctypes.POINTER(SilKit_LinController)

SilKit_LinFrameStatusHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrameStatusEvent)
)

SilKit_LinGoToSleepHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinGoToSleepEvent)
)

SilKit_LinWakeupHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinWakeupEvent)
)

SilKit_Experimental_LinSlaveConfigurationHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_Experimental_LinSlaveConfigurationEvent)
)

SilKit_Experimental_LinFrameHeaderHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_Experimental_LinFrameHeaderEvent)
)

SilKit_LinController_Create = _silkit_.SilKit_LinController_Create
SilKit_LinController_Create.restype = SilKit_ReturnCode
SilKit_LinController_Create.argtypes = [
    ctypes.POINTER(SilKit_LinController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
]
SilKit_LinController_Create.errcheck = check_silkit_status
SilKit_LinController_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_LinController_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.c_char_p
)

SilKit_LinController_Init = _silkit_.SilKit_LinController_Init
SilKit_LinController_Init.restype = SilKit_ReturnCode
SilKit_LinController_Init.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinControllerConfig)
]
SilKit_LinController_Init.errcheck = check_silkit_status
SilKit_LinController_Init_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinControllerConfig)
)

SilKit_Experimental_LinController_InitDynamic = _silkit_.SilKit_Experimental_LinController_InitDynamic
SilKit_Experimental_LinController_InitDynamic.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_InitDynamic.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_Experimental_LinControllerDynamicConfig)
]
SilKit_Experimental_LinController_InitDynamic.errcheck = check_silkit_status
SilKit_Experimental_LinController_InitDynamic_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_Experimental_LinControllerDynamicConfig)
)

SilKit_LinController_SetFrameResponse = _silkit_.SilKit_LinController_SetFrameResponse
SilKit_LinController_SetFrameResponse.restype = SilKit_ReturnCode
SilKit_LinController_SetFrameResponse.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrameResponse)
]
SilKit_LinController_SetFrameResponse.errcheck = check_silkit_status
SilKit_LinController_SetFrameResponse_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrameResponse)
)


SilKit_Experimental_LinController_SendDynamicResponse = _silkit_.SilKit_Experimental_LinController_SendDynamicResponse
SilKit_Experimental_LinController_SendDynamicResponse.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_SendDynamicResponse.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrame)
]
SilKit_Experimental_LinController_SendDynamicResponse.errcheck = check_silkit_status
SilKit_Experimental_LinController_SendDynamicResponse_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrame)
)


SilKit_LinController_Status = _silkit_.SilKit_LinController_Status
SilKit_LinController_Status.restype = SilKit_ReturnCode
SilKit_LinController_Status.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinControllerStatus)
]
SilKit_LinController_Status.errcheck = check_silkit_status
SilKit_LinController_Status_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinControllerStatus)
)

SilKit_LinController_SendFrame = _silkit_.SilKit_LinController_SendFrame
SilKit_LinController_SendFrame.restype = SilKit_ReturnCode
SilKit_LinController_SendFrame.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrame),
    SilKit_LinFrameResponseType
]
SilKit_LinController_SendFrame.errcheck = check_silkit_status

SilKit_LinController_SendFrame_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrame),
    SilKit_LinFrameResponseType
)

SilKit_LinController_SendFrameHeader = _silkit_.SilKit_LinController_SendFrameHeader
SilKit_LinController_SendFrameHeader.restype = SilKit_ReturnCode
SilKit_LinController_SendFrameHeader.argtypes = [
    SilKit_LinController_p,
    SilKit_LinId
]
SilKit_LinController_SendFrameHeader.errcheck = check_silkit_status
SilKit_LinController_SendFrameHeader_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    SilKit_LinId
)

SilKit_LinController_UpdateTxBuffer = _silkit_.SilKit_LinController_UpdateTxBuffer
SilKit_LinController_UpdateTxBuffer.restype = SilKit_ReturnCode
SilKit_LinController_UpdateTxBuffer.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrame)
]
SilKit_LinController_UpdateTxBuffer.errcheck = check_silkit_status
SilKit_LinController_UpdateTxBuffer_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_LinFrame)
)

SilKit_LinController_GoToSleep = _silkit_.SilKit_LinController_GoToSleep
SilKit_LinController_GoToSleep.restype = SilKit_ReturnCode
SilKit_LinController_GoToSleep.argtypes = [
    SilKit_LinController_p
]
SilKit_LinController_GoToSleep.errcheck = check_silkit_status
SilKit_LinController_GoToSleep_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p
)

SilKit_LinController_GoToSleepInternal = _silkit_.SilKit_LinController_GoToSleepInternal
SilKit_LinController_GoToSleepInternal.restype = SilKit_ReturnCode
SilKit_LinController_GoToSleepInternal.argtypes = [
    SilKit_LinController_p
]
SilKit_LinController_GoToSleepInternal.errcheck = check_silkit_status
SilKit_LinController_GoToSleepInternal_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p
)

SilKit_LinController_Wakeup = _silkit_.SilKit_LinController_Wakeup
SilKit_LinController_Wakeup.restype = SilKit_ReturnCode
SilKit_LinController_Wakeup.argtypes = [
    SilKit_LinController_p
]
SilKit_LinController_Wakeup.errcheck = check_silkit_status
SilKit_LinController_Wakeup_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p
)


SilKit_LinController_WakeupInternal = _silkit_.SilKit_LinController_WakeupInternal
SilKit_LinController_WakeupInternal.restype = SilKit_ReturnCode
SilKit_LinController_WakeupInternal.argtypes = [
    SilKit_LinController_p
]
SilKit_LinController_WakeupInternal.errcheck = check_silkit_status

SilKit_LinController_WakeupInternal_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p
)

SilKit_Experimental_LinController_GetSlaveConfiguration = _silkit_.SilKit_Experimental_LinController_GetSlaveConfiguration
SilKit_Experimental_LinController_GetSlaveConfiguration.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_GetSlaveConfiguration.argtypes = [
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_Experimental_LinSlaveConfiguration)
]
SilKit_Experimental_LinController_GetSlaveConfiguration.errcheck = check_silkit_status
SilKit_Experimental_LinController_GetSlaveConfiguration_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.POINTER(SilKit_Experimental_LinSlaveConfiguration)
)

SilKit_LinController_AddFrameStatusHandler = _silkit_.SilKit_LinController_AddFrameStatusHandler
SilKit_LinController_AddFrameStatusHandler.restype = SilKit_ReturnCode
SilKit_LinController_AddFrameStatusHandler.argtypes = [
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_LinFrameStatusHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_LinController_AddFrameStatusHandler.errcheck = check_silkit_status
SilKit_LinController_AddFrameStatusHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_LinFrameStatusHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_LinController_RemoveFrameStatusHandler = _silkit_.SilKit_LinController_RemoveFrameStatusHandler
SilKit_LinController_RemoveFrameStatusHandler.restype = SilKit_ReturnCode
SilKit_LinController_RemoveFrameStatusHandler.argtypes = [
    SilKit_LinController_p,
    SilKit_HandlerId
]
SilKit_LinController_RemoveFrameStatusHandler.errcheck = check_silkit_status
SilKit_LinController_RemoveFrameStatusHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    SilKit_HandlerId
)

# The GoToSleepHandler is called whenever a go-to-sleep frame
# was received.
# Note: The LIN controller does not automatically enter sleep
# mode up reception of a go-to-sleep frame. I.e.,
# SilKit_LinController_GoToSleepInternal() must be called manually
# Note: This handler will always be called, independently of the
# SilKit_LinFrameResponseMode configuration for LIN ID 0x3C. However,
# regarding the SilKit_LinFrameStatusHandler, the go-to-sleep frame is
# treated like every other frame, i.e. the SilKit_LinFrameStatusHandler is
# only called for LIN ID 0x3C if configured as
# SilKit_LinFrameResponseMode_Rx.
SilKit_LinController_AddGoToSleepHandler = _silkit_.SilKit_LinController_AddGoToSleepHandler
SilKit_LinController_AddGoToSleepHandler.restype = SilKit_ReturnCode
SilKit_LinController_AddGoToSleepHandler.argtypes = [
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_LinGoToSleepHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_LinController_AddGoToSleepHandler.errcheck = check_silkit_status
SilKit_LinController_AddGoToSleepHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_LinGoToSleepHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_LinController_RemoveGoToSleepHandler = _silkit_.SilKit_LinController_RemoveGoToSleepHandler
SilKit_LinController_RemoveGoToSleepHandler.restype = SilKit_ReturnCode
SilKit_LinController_RemoveGoToSleepHandler.argtypes = [
    SilKit_LinController_p,
    SilKit_HandlerId
]
SilKit_LinController_RemoveGoToSleepHandler.errcheck = check_silkit_status
SilKit_LinController_RemoveGoToSleepHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    SilKit_HandlerId
)

# The WakeupHandler is called whenever a wake up pulse is received
# Note: The LIN controller does not automatically enter
# operational mode on wake up pulse detection. I.e.,
# WakeInternal() must be called manually.
SilKit_LinController_AddWakeupHandler = _silkit_.SilKit_LinController_AddWakeupHandler
SilKit_LinController_AddWakeupHandler.restype = SilKit_ReturnCode
SilKit_LinController_AddWakeupHandler.argtypes = [
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_LinWakeupHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_LinController_AddWakeupHandler.errcheck = check_silkit_status
SilKit_LinController_AddWakeupHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_LinWakeupHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_LinController_RemoveWakeupHandler = _silkit_.SilKit_LinController_RemoveWakeupHandler
SilKit_LinController_RemoveWakeupHandler.restype = SilKit_ReturnCode
SilKit_LinController_RemoveWakeupHandler.argtypes = [
    SilKit_LinController_p,
    SilKit_HandlerId
]
SilKit_LinController_RemoveWakeupHandler.errcheck = check_silkit_status
SilKit_LinController_RemoveWakeupHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    SilKit_HandlerId
)

# The LinSlaveConfigurationHandler is called whenever a remote LIN Slave is configured via SilKit_LinController_Init
# Note: This callback is mainly for diagnostic purposes and is NOT needed for regular LIN controller operation. 
# It can be used to call SilKit_Experimental_LinController_GetSlaveConfiguration to keep track of LIN Ids, where
# a response of a LIN Slave is to be expected.
# Requires SilKit_LinControllerMode_Master
SilKit_Experimental_LinController_AddLinSlaveConfigurationHandler = _silkit_.SilKit_Experimental_LinController_AddLinSlaveConfigurationHandler
SilKit_Experimental_LinController_AddLinSlaveConfigurationHandler.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_AddLinSlaveConfigurationHandler.argtypes = [
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_Experimental_LinSlaveConfigurationHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_Experimental_LinController_AddLinSlaveConfigurationHandler.errcheck = check_silkit_status
SilKit_Experimental_LinController_AddLinSlaveConfigurationHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_Experimental_LinSlaveConfigurationHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_Experimental_LinController_RemoveLinSlaveConfigurationHandler = _silkit_.SilKit_Experimental_LinController_RemoveLinSlaveConfigurationHandler
SilKit_Experimental_LinController_RemoveLinSlaveConfigurationHandler.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_RemoveLinSlaveConfigurationHandler.argtypes = [
    SilKit_LinController_p,
    SilKit_HandlerId
]
SilKit_Experimental_LinController_RemoveLinSlaveConfigurationHandler.errcheck = check_silkit_status
SilKit_Experimental_LinController_RemoveLinSlaveConfigurationHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    SilKit_HandlerId
)

SilKit_Experimental_LinController_AddFrameHeaderHandler = _silkit_.SilKit_Experimental_LinController_AddFrameHeaderHandler
SilKit_Experimental_LinController_AddFrameHeaderHandler.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_AddFrameHeaderHandler.argtypes = [
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_Experimental_LinFrameHeaderHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
]
SilKit_Experimental_LinController_AddFrameHeaderHandler.errcheck = check_silkit_status
SilKit_Experimental_LinController_AddFrameHeaderHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    ctypes.c_void_p,
    SilKit_Experimental_LinFrameHeaderHandler_t,
    ctypes.POINTER(SilKit_HandlerId)
)

SilKit_Experimental_LinController_RemoveFrameHeaderHandler = _silkit_.SilKit_Experimental_LinController_RemoveFrameHeaderHandler
SilKit_Experimental_LinController_RemoveFrameHeaderHandler.restype = SilKit_ReturnCode
SilKit_Experimental_LinController_RemoveFrameHeaderHandler.argtypes = [
    SilKit_LinController_p,
    SilKit_HandlerId
]
SilKit_Experimental_LinController_RemoveFrameHeaderHandler.errcheck = check_silkit_status
SilKit_Experimental_LinController_RemoveFrameHeaderHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_LinController_p,
    SilKit_HandlerId
)

###### DataPubSub.h ######

class SilKit_DataSpec(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("topic", ctypes.c_char_p),
        ("mediaType", ctypes.c_char_p),
        ("labelList", SilKit_LabelList)
    ]

class SilKit_DataMessageEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("timestamp", SilKit_NanosecondsTime),
        ("data", SilKit_ByteVector)
    ]

class SilKit_DataPublisher(ctypes.Structure):
    _pack_ = 8
SilKit_DataPublisher_p = ctypes.POINTER(SilKit_DataPublisher)

class SilKit_DataSubscriber(ctypes.Structure):
    _pack_ = 8
SilKit_DataSubscriber_p = ctypes.POINTER(SilKit_DataSubscriber)

SilKit_DataMessageHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_DataSubscriber_p,
    ctypes.POINTER(SilKit_DataMessageEvent)
)

SilKit_DataPublisher_Create = _silkit_.SilKit_DataPublisher_Create
SilKit_DataPublisher_Create.restype = SilKit_ReturnCode
SilKit_DataPublisher_Create.argtypes = [
    ctypes.POINTER(SilKit_DataPublisher_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_DataSpec),
    ctypes.c_ubyte
]
SilKit_DataPublisher_Create.errcheck = check_silkit_status
SilKit_DataPublisher_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_DataPublisher_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_DataSpec),
    ctypes.c_ubyte
)

SilKit_DataSubscriber_Create = _silkit_.SilKit_DataSubscriber_Create
SilKit_DataSubscriber_Create.restype = SilKit_ReturnCode
SilKit_DataSubscriber_Create.argtypes = [
    ctypes.POINTER(SilKit_DataSubscriber_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_DataSpec),
    ctypes.c_void_p,
    SilKit_DataMessageHandler_t
]
SilKit_DataSubscriber_Create.errcheck = check_silkit_status
SilKit_DataSubscriber_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_DataSubscriber_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_DataSpec),
    ctypes.c_void_p,
    SilKit_DataMessageHandler_t
)

SilKit_DataPublisher_Publish = _silkit_.SilKit_DataPublisher_Publish
SilKit_DataPublisher_Publish.restype = SilKit_ReturnCode
SilKit_DataPublisher_Publish.argtypes = [
    SilKit_DataPublisher_p,
    ctypes.POINTER(SilKit_ByteVector),
]
SilKit_DataPublisher_Publish.errcheck = check_silkit_status
SilKit_DataPublisher_Publish_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_DataPublisher_p,
    ctypes.POINTER(SilKit_ByteVector)
)

SilKit_DataSubscriber_SetDataMessageHandler = _silkit_.SilKit_DataSubscriber_SetDataMessageHandler
SilKit_DataSubscriber_SetDataMessageHandler.restype = SilKit_ReturnCode
SilKit_DataSubscriber_SetDataMessageHandler.argtypes = [
    SilKit_DataSubscriber_p,
    ctypes.c_void_p,
    SilKit_DataMessageHandler_t
]
SilKit_DataSubscriber_SetDataMessageHandler.errcheck = check_silkit_status
SilKit_DataSubscriber_SetDataMessageHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_DataSubscriber_p,
    ctypes.c_void_p,
    SilKit_DataMessageHandler_t
)

###### EventProducer.h ######

class SilKit_Experimental_EventProducer(ctypes.Structure):
    _pack_ = 8
class SilKit_Experimental_CanEventProducer(ctypes.Structure):
    _pack_ = 8
class SilKit_Experimental_FlexRayEventProducer(ctypes.Structure):
    _pack_ = 8
class SilKit_Experimental_EthernetEventProducer(ctypes.Structure):
    _pack_ = 8
class SilKit_Experimental_LinEventProducer(ctypes.Structure):
    _pack_ = 8

SilKit_Experimental_ControllerDescriptor = ctypes.c_uint64
SilKit_Experimental_ControllerDescriptor_Invalid = 0

class  SilKit_Experimental_EventReceivers(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("numReceivers", ctypes.c_size_t),
        ("controllerDescriptors", ctypes.POINTER(SilKit_Experimental_ControllerDescriptor))
    ]

SilKit_Experimental_CanEventProducer_Produce = _silkit_.SilKit_Experimental_CanEventProducer_Produce
SilKit_Experimental_CanEventProducer_Produce.restype = SilKit_ReturnCode
SilKit_Experimental_CanEventProducer_Produce.argtypes = [
    ctypes.POINTER(SilKit_Experimental_CanEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers),
]
SilKit_Experimental_CanEventProducer_Produce.errcheck = check_silkit_status
SilKit_Experimental_CanEventProducer_Produce_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Experimental_CanEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers)
)

SilKit_Experimental_FlexRayEventProducer_Produce = _silkit_.SilKit_Experimental_FlexRayEventProducer_Produce
SilKit_Experimental_FlexRayEventProducer_Produce.restype = SilKit_ReturnCode
SilKit_Experimental_FlexRayEventProducer_Produce.argtypes = [
    ctypes.POINTER(SilKit_Experimental_FlexRayEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers),
]
SilKit_Experimental_FlexRayEventProducer_Produce.errcheck = check_silkit_status
SilKit_Experimental_FlexRayEventProducer_Produce_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Experimental_FlexRayEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers)
)

SilKit_Experimental_EthernetEventProducer_Produce = _silkit_.SilKit_Experimental_EthernetEventProducer_Produce
SilKit_Experimental_EthernetEventProducer_Produce.restype = SilKit_ReturnCode
SilKit_Experimental_EthernetEventProducer_Produce.argtypes = [
    ctypes.POINTER(SilKit_Experimental_EthernetEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers),
]
SilKit_Experimental_EthernetEventProducer_Produce.errcheck = check_silkit_status
SilKit_Experimental_EthernetEventProducer_Produce_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Experimental_EthernetEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers)
)

SilKit_Experimental_LinEventProducer_Produce = _silkit_.SilKit_Experimental_LinEventProducer_Produce
SilKit_Experimental_LinEventProducer_Produce.restype = SilKit_ReturnCode
SilKit_Experimental_LinEventProducer_Produce.argtypes = [
    ctypes.POINTER(SilKit_Experimental_LinEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers),
]
SilKit_Experimental_LinEventProducer_Produce.errcheck = check_silkit_status
SilKit_Experimental_LinEventProducer_Produce_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Experimental_LinEventProducer),
    ctypes.POINTER(SilKit_StructHeader),
    ctypes.POINTER(SilKit_Experimental_EventReceivers)
)

###### Rpc.h ######

class SilKit_RpcSpec(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("functionName", ctypes.c_char_p),
        ("mediaType", ctypes.c_char_p),
        ("labelList", SilKit_LabelList)
    ]

class SilKit_RpcCallHandle(ctypes.Structure):
    _pack_ = 8
SilKit_RpcCallHandle_p = ctypes.POINTER(SilKit_RpcCallHandle)

class SilKit_RpcServer(ctypes.Structure):
    _pack_ = 8
SilKit_RpcServer_p = ctypes.POINTER(SilKit_RpcServer)

class SilKit_RpcClient(ctypes.Structure):
    _pack_ = 8
SilKit_RpcClient_p = ctypes.POINTER(SilKit_RpcClient)

SilKit_RpcCallStatus = ctypes.c_uint32
class SilKitRpcCallStatus(enum.IntEnum):
    SUCCESS = 0
    SERVER_NOT_REACHABLE = 1
    UNDEFINED_ERROR = 2
    INTERNAL_SERVER_ERROR = 3
    TIMEOUT = 4

class SilKit_RpcCallEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("timestamp", SilKit_NanosecondsTime),
        ("callHandle", SilKit_RpcCallHandle_p),
        ("argumentData", SilKit_ByteVector)
    ]

class SilKit_RpcCallResultEvent(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("timestamp", SilKit_NanosecondsTime),
        ("userContext", ctypes.c_void_p),
        ("callStatus", SilKit_RpcCallStatus),
        ("resultData", SilKit_ByteVector)
    ]

SilKit_RpcCallHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_RpcClient_p,
    ctypes.POINTER(SilKit_RpcCallEvent)
)

SilKit_RpcCallResultHandler_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    SilKit_RpcClient_p,
    ctypes.POINTER(SilKit_RpcCallResultEvent)
)

SilKit_RpcServer_Create = _silkit_.SilKit_RpcServer_Create
SilKit_RpcServer_Create.restype = SilKit_ReturnCode
SilKit_RpcServer_Create.argtypes = [
    ctypes.POINTER(SilKit_RpcServer_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_RpcSpec),
    ctypes.c_void_p,
    SilKit_RpcCallHandler_t
]
SilKit_RpcServer_Create.errcheck = check_silkit_status
SilKit_RpcServer_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_RpcServer_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_RpcSpec),
    ctypes.c_void_p,
    SilKit_RpcCallHandler_t
)

SilKit_RpcServer_SubmitResult = _silkit_.SilKit_RpcServer_SubmitResult
SilKit_RpcServer_SubmitResult.restype = SilKit_ReturnCode
SilKit_RpcServer_SubmitResult.argtypes = [
    SilKit_RpcServer_p,
    SilKit_RpcCallHandle_p,
    ctypes.POINTER(SilKit_ByteVector),
]
SilKit_RpcServer_SubmitResult.errcheck = check_silkit_status
SilKit_RpcServer_SubmitResult_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_RpcServer_p,
    SilKit_RpcCallHandle_p,
    ctypes.POINTER(SilKit_ByteVector)
)

SilKit_RpcServer_SetCallHandler = _silkit_.SilKit_RpcServer_SetCallHandler
SilKit_RpcServer_SetCallHandler.restype = SilKit_ReturnCode
SilKit_RpcServer_SetCallHandler.argtypes = [
    SilKit_RpcServer_p,
    ctypes.c_void_p,
    SilKit_RpcCallHandler_t
]
SilKit_RpcServer_SetCallHandler.errcheck = check_silkit_status
SilKit_RpcServer_SetCallHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_RpcServer_p,
    ctypes.c_void_p,
    SilKit_RpcCallHandler_t
)

SilKit_RpcClient_Create = _silkit_.SilKit_RpcClient_Create
SilKit_RpcClient_Create.restype = SilKit_ReturnCode
SilKit_RpcClient_Create.argtypes = [
    ctypes.POINTER(SilKit_RpcClient_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_RpcSpec),
    ctypes.c_void_p,
    SilKit_RpcCallResultHandler_t
]
SilKit_RpcClient_Create.errcheck = check_silkit_status
SilKit_RpcClient_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_RpcClient_p),
    SilKit_Participant_p,
    ctypes.c_char_p,
    ctypes.POINTER(SilKit_RpcSpec),
    ctypes.c_void_p,
    SilKit_RpcCallResultHandler_t
)

SilKit_RpcClient_Call = _silkit_.SilKit_RpcClient_Call
SilKit_RpcClient_Call.restype = SilKit_ReturnCode
SilKit_RpcClient_Call.argtypes = [
    SilKit_RpcClient_p,
    ctypes.POINTER(SilKit_ByteVector),
    ctypes.c_void_p
]
SilKit_RpcClient_Call.errcheck = check_silkit_status
SilKit_RpcClient_Call_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_RpcClient_p,
    ctypes.POINTER(SilKit_ByteVector),
    ctypes.c_void_p
)

SilKit_RpcClient_CallWithTimeout = _silkit_.SilKit_RpcClient_CallWithTimeout
SilKit_RpcClient_CallWithTimeout.restype = SilKit_ReturnCode
SilKit_RpcClient_CallWithTimeout.argtypes = [
    SilKit_RpcClient_p,
    ctypes.POINTER(SilKit_ByteVector),
    SilKit_NanosecondsTime,
    ctypes.c_void_p
]
SilKit_RpcClient_CallWithTimeout.errcheck = check_silkit_status
SilKit_RpcClient_CallWithTimeout_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_RpcClient_p,
    ctypes.POINTER(SilKit_ByteVector),
    SilKit_NanosecondsTime,
    ctypes.c_void_p
)

SilKit_RpcClient_SetCallResultHandler = _silkit_.SilKit_RpcClient_SetCallResultHandler
SilKit_RpcClient_SetCallResultHandler.restype = SilKit_ReturnCode
SilKit_RpcClient_SetCallResultHandler.argtypes = [
    SilKit_RpcClient_p,
    ctypes.c_void_p,
    SilKit_RpcCallResultHandler_t
]
SilKit_RpcClient_SetCallResultHandler.errcheck = check_silkit_status
SilKit_RpcClient_SetCallResultHandler_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_RpcClient_p,
    ctypes.c_void_p,
    SilKit_RpcCallResultHandler_t
)

###### NetworkSimulator.h ######

SilKit_Experimental_SimulatedNetworkType = ctypes.c_uint32
class SilKitExperimentalSimulatedNetworkType(enum.IntEnum):
    UNDEFINED = 0
    CAN = 1
    LIN = 2
    ETHERNET = 3
    FLEXRAY = 4

class SilKit_Experimental_NetworkSimulator(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_NetworkSimulator_p = ctypes.POINTER(SilKit_Experimental_NetworkSimulator)
class SilKit_Experimental_SimulatedNetwork(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedNetwork_p = ctypes.POINTER(SilKit_Experimental_SimulatedNetwork)
class SilKit_Experimental_SimulatedNetworkFunctions(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedNetworkFunctions_p = ctypes.POINTER(SilKit_Experimental_SimulatedNetworkFunctions)
class SilKit_Experimental_SimulatedCanController(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedCanController_p = ctypes.POINTER(SilKit_Experimental_SimulatedCanController)
class SilKit_Experimental_SimulatedFlexRayController(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedFlexRayController_p = ctypes.POINTER(SilKit_Experimental_SimulatedFlexRayController)
class SilKit_Experimental_SimulatedControllerFunctions(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedControllerFunctions_p = ctypes.POINTER(SilKit_Experimental_SimulatedControllerFunctions)
class SilKit_Experimental_SimulatedCanControllerFunctions(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedCanControllerFunctions_p = ctypes.POINTER(SilKit_Experimental_SimulatedCanControllerFunctions)
class SilKit_Experimental_SimulatedFlexRayControllerFunctions(ctypes.Structure):
    _pack_ = 8
SilKit_Experimental_SimulatedFlexRayControllerFunctions_p = ctypes.POINTER(SilKit_Experimental_SimulatedFlexRayControllerFunctions)

SilKit_Experimental_SimulatedNetwork_ProvideSimulatedController_t = ctypes.CFUNCTYPE(
    None,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(ctypes.c_void_p),
    SilKit_Experimental_ControllerDescriptor,
    ctypes.c_void_p
)
SilKit_Experimental_SimulatedNetwork_SimulatedControllerRemoved_t = ctypes.CFUNCTYPE(
    None,
    SilKit_Experimental_ControllerDescriptor,
    ctypes.c_void_p
)
SilKit_Experimental_SimulatedNetwork_SetEventProducer_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_void_p
)
class SilKit_Experimental_SimulatedNetworkFunctions(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("ProvideSimulatedController", SilKit_Experimental_SimulatedNetwork_ProvideSimulatedController_t),
        ("SimulatedControllerRemoved", SilKit_Experimental_SimulatedNetwork_SimulatedControllerRemoved_t),
        ("SetEventProducer", SilKit_Experimental_SimulatedNetwork_SetEventProducer_t)
    ]

class SilKit_Experimental_NetSim_CanFrameRequest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader), # The interface id specifying which version of this struct was obtained
        ("frame", SilKit_CanFrame), # The CAN Frame that corresponds to the meta data
        ("userContext", ctypes.c_void_p), # Optional pointer provided by user when sending the frame
    ]

class SilKit_Experimental_NetSim_CanConfigureBaudrate(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("rate", ctypes.c_uint32),
        ("fdRate", ctypes.c_uint32),
        ("xlRate", ctypes.c_uint32)
    ]

SilKit_Experimental_NetSim_CanControllerModeFlags = ctypes.c_int32
class SilKitExperimentalNetSimCanControllerModeFlags(enum.IntEnum):
    RESET_ERROR_HANDLING = BIT(0) # Reset the error counters to zero and the error state to error active.
    CANCEL_TRANSMIT_REQUESTS = BIT(1) # Cancel all outstanding transmit requests (flush transmit queue of controller).

class SilKit_Experimental_NetSim_CanControllerMode(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("canControllerModeFlags", SilKit_Experimental_NetSim_CanControllerModeFlags),
        ("state", SilKit_CanControllerState)
    ]

SilKit_Experimental_SimulatedCan_OnSetBaudrate_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_CanConfigureBaudrate)
)
SilKit_Experimental_SimulatedCan_OnFrameRequest_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_CanFrameRequest)
)
SilKit_Experimental_SimulatedCan_OnSetControllerMode_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_CanControllerMode)
)
class SilKit_Experimental_SimulatedCanControllerFunctions(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("OnSetBaudrate", SilKit_Experimental_SimulatedCan_OnSetBaudrate_t),
        ("OnFrameRequest", SilKit_Experimental_SimulatedCan_OnFrameRequest_t),
        ("OnSetControllerMode", SilKit_Experimental_SimulatedCan_OnSetControllerMode_t)
    ]

class SilKit_Experimental_NetSim_FlexrayHostCommand(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("chiCommand", SilKit_FlexrayChiCommand)
    ]

class SilKit_Experimental_NetSim_FlexrayControllerConfig(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        # FlexRay cluster parameters
        ("clusterParams", ctypes.POINTER(SilKit_FlexrayClusterParameters)),
        # FlexRay node parameters
        ("nodeParams", ctypes.POINTER(SilKit_FlexrayNodeParameters)),
        # FlexRay buffer configs
        ("numBufferConfigs", ctypes.c_uint32),
        ("bufferConfigs", ctypes.POINTER(SilKit_FlexrayTxBufferConfig))
    ]

class SilKit_Experimental_NetSim_FlexrayTxBufferConfigUpdate(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("txBufferIdx", ctypes.c_uint16),
        ("txBufferConfig", ctypes.POINTER(SilKit_FlexrayTxBufferConfig))
    ]

class SilKit_Experimental_NetSim_FlexrayTxBufferUpdate(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        # The interface id specifying which version of this struct was obtained
        ("structHeader", SilKit_StructHeader),
        # Index of the TX Buffers according to the configured buffers (cf. FlexrayControllerConfig).
        ("txBufferIndex", ctypes.c_uint16),
        # Payload data valid flag
        ("payloadDataValid", SilKit_Bool),
        # Raw payload containing 0 to 254 bytes.
        ("payload", SilKit_ByteVector)
    ]

SilKit_Experimental_SimulatedFlexRay_OnHostCommand_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_FlexrayHostCommand)
)
SilKit_Experimental_SimulatedFlexRay_OnControllerConfig_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_FlexrayControllerConfig)
)
SilKit_Experimental_SimulatedFlexRay_OnTxBufferConfigUpdate_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_FlexrayTxBufferConfigUpdate)
)
SilKit_Experimental_SimulatedFlexRay_OnTxBufferUpdate_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_FlexrayTxBufferUpdate)
)
class SilKit_Experimental_SimulatedFlexRayControllerFunctions(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("OnHostCommand", SilKit_Experimental_SimulatedFlexRay_OnHostCommand_t),
        ("OnControllerConfig", SilKit_Experimental_SimulatedFlexRay_OnControllerConfig_t),
        ("OnTxBufferConfigUpdate", SilKit_Experimental_SimulatedFlexRay_OnTxBufferConfigUpdate_t),
        ("OnTxBufferUpdate", SilKit_Experimental_SimulatedFlexRay_OnTxBufferUpdate_t)
    ]

class SilKit_Experimental_NetSim_EthernetFrameRequest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("ethernetFrame", ctypes.POINTER(SilKit_EthernetFrame)),
        ("userContext", ctypes.c_void_p),# Optional pointer provided by user when sending the frame
    ]

SilKit_EthernetControllerMode = ctypes.c_ubyte
class SilKitEthernetControllerMode(enum.IntEnum):
    INACTIVE = 0
    ACTIVE = 1

class SilKit_Experimental_NetSim_EthernetControllerMode(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("mode", SilKit_EthernetControllerMode)
    ]

SilKit_Experimental_SimulatedEthernet_OnFrameRequest_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_EthernetFrameRequest)
)
SilKit_Experimental_SimulatedEthernet_OnSetControllerMode_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_EthernetControllerMode)
)
class SilKit_Experimental_SimulatedEthernetControllerFunctions(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("OnFrameRequest", SilKit_Experimental_SimulatedEthernet_OnFrameRequest_t),
        ("OnSetControllerMode", SilKit_Experimental_SimulatedEthernet_OnSetControllerMode_t)
    ]

SilKit_Experimental_NetSim_LinSimulationMode = ctypes.c_ubyte
class SilKitExperimentalNetSimLinSimulationMode(enum.IntEnum):
    DEFAULT = 0
    DYNAMIC = 1

class SilKit_Experimental_NetSim_LinFrameRequest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("frame", ctypes.POINTER(SilKit_LinFrame)),
        ("responseType", SilKit_LinFrameResponseType)
    ]

class SilKit_Experimental_NetSim_LinFrameHeaderRequest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("id", SilKit_LinId)
    ]

class SilKit_Experimental_NetSim_LinWakeupPulse(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("timestamp", SilKit_NanosecondsTime),# Timestamp of the wakeup pulse
    ]

class SilKit_Experimental_NetSim_LinControllerConfig(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("controllerMode", SilKit_LinControllerMode),
        ("baudRate", SilKit_LinBaudRate),
        ("numFrameResponses", ctypes.c_size_t),
        ("frameResponses", ctypes.POINTER(SilKit_LinFrameResponse)),
        ("simulationMode", SilKit_Experimental_NetSim_LinSimulationMode)
    ]

class SilKit_Experimental_NetSim_LinFrameResponseUpdate(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("numFrameResponses", ctypes.c_size_t),
        ("frameResponses", ctypes.POINTER(SilKit_LinFrameResponse))
    ]

class SilKit_Experimental_NetSim_LinControllerStatusUpdate(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),# The interface id specifying which version of this struct was obtained
        ("status", SilKit_LinControllerStatus),
        ("timestamp", SilKit_NanosecondsTime),# Timestamp of the wakeup pulse
    ]

SilKit_Experimental_SimulatedLin_OnFrameRequest_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_LinFrameRequest)
)
SilKit_Experimental_SimulatedLin_OnFrameHeaderRequest_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_LinFrameHeaderRequest)
)
SilKit_Experimental_SimulatedLin_OnWakeupPulse_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_LinWakeupPulse)
)
SilKit_Experimental_SimulatedLin_OnControllerConfig_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_LinControllerConfig)
)
SilKit_Experimental_SimulatedLin_OnFrameResponseUpdate_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_LinFrameResponseUpdate)
)
SilKit_Experimental_SimulatedLin_OnControllerStatusUpdate_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_NetSim_LinControllerStatusUpdate)
)
class SilKit_Experimental_SimulatedLinControllerFunctions(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("structHeader", SilKit_StructHeader),
        ("OnFrameRequest", SilKit_Experimental_SimulatedLin_OnFrameRequest_t),
        ("OnFrameHeaderRequest", SilKit_Experimental_SimulatedLin_OnFrameHeaderRequest_t),
        ("OnWakeupPulse", SilKit_Experimental_SimulatedLin_OnWakeupPulse_t),
        ("OnControllerConfig", SilKit_Experimental_SimulatedLin_OnControllerConfig_t),
        ("OnFrameResponseUpdate", SilKit_Experimental_SimulatedLin_OnFrameResponseUpdate_t),
        ("OnControllerStatusUpdate", SilKit_Experimental_SimulatedLin_OnControllerStatusUpdate_t)
    ]

SilKit_Experimental_NetworkSimulator_Create = _silkit_.SilKit_Experimental_NetworkSimulator_Create
SilKit_Experimental_NetworkSimulator_Create.restype = SilKit_ReturnCode
SilKit_Experimental_NetworkSimulator_Create.argtypes = [
    ctypes.POINTER(SilKit_Experimental_NetworkSimulator_p),
    SilKit_Participant_p
]
SilKit_Experimental_NetworkSimulator_Create.errcheck = check_silkit_status
SilKit_Experimental_NetworkSimulator_Create_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    ctypes.POINTER(SilKit_Experimental_NetworkSimulator_p),
    SilKit_Participant_p
)

SilKit_Experimental_NetworkSimulator_SimulateNetwork = _silkit_.SilKit_Experimental_NetworkSimulator_SimulateNetwork
SilKit_Experimental_NetworkSimulator_SimulateNetwork.restype = SilKit_ReturnCode
SilKit_Experimental_NetworkSimulator_SimulateNetwork.argtypes = [
    SilKit_Experimental_NetworkSimulator_p,
    ctypes.c_char_p,
    SilKit_Experimental_SimulatedNetworkType,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_SimulatedNetworkFunctions)
]
SilKit_Experimental_NetworkSimulator_SimulateNetwork.errcheck = check_silkit_status
SilKit_Experimental_NetworkSimulator_SimulateNetwork_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Experimental_NetworkSimulator_p,
    ctypes.c_char_p,
    SilKit_Experimental_SimulatedNetworkType,
    ctypes.c_void_p,
    ctypes.POINTER(SilKit_Experimental_SimulatedNetworkFunctions)
)

SilKit_Experimental_NetworkSimulator_Start = _silkit_.SilKit_Experimental_NetworkSimulator_Start
SilKit_Experimental_NetworkSimulator_Start.restype = SilKit_ReturnCode
SilKit_Experimental_NetworkSimulator_Start.argtypes = [
    SilKit_Experimental_NetworkSimulator_p
]
SilKit_Experimental_NetworkSimulator_Start.errcheck = check_silkit_status
SilKit_Experimental_NetworkSimulator_Start_t = ctypes.CFUNCTYPE(
    SilKit_ReturnCode,
    SilKit_Experimental_NetworkSimulator_p
)
