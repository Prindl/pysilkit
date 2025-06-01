import ctypes
import pathlib
import subprocess
import time

from .library import silkitapi
from .time_master import SilKitTimeMaster

_base_path_ = pathlib.Path(__file__).parent

class SilKit(object):
    def __init__(self, *participants, port=8500, launch_monitor=False):
        self.listen_uri = f"silkit://localhost:{port}"
        # Start the Middleware Registry
        self.mw_log = open("sil_kit_registry.log", "w")
        self.middleware = subprocess.Popen(
            [
                str(_base_path_ / "library/sil-kit-registry.exe"),
                "--listen-uri", self.listen_uri,
                "--log", "trace" # trace, debug, warn, info, error, critical or off
             ],
            stdout=self.mw_log
        )
        self.sc_log = open("sil_kit_system_controller.log", "w")
        self.system_controller = subprocess.Popen(
            # Start the System Controller and tell it to wait for participants
            [
                str(_base_path_ / "library/sil-kit-system-controller.exe"),
                "--name", "SystemController",
                "--connect-uri", self.listen_uri,
                "--log", "trace" # trace, debug, warn, info, error, critical or off
            ] + list(participants),
            stdout=self.sc_log
        )
        self.launch_monitor = launch_monitor
        if self.launch_monitor:
            self.system_monitor = subprocess.Popen(
                # Start the System Controller and tell it to wait for participants
                [
                    str(_base_path_ / "library/sil-kit-monitor.exe"),
                    "--name", "SystemMonitor",
                    "--connect-uri", self.listen_uri
                ],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        #Create a time master to provide timestamps
        self.time_master = SilKitTimeMaster(port)
        self.time_master.start()
        print(f"Using SilKit {self.version()}")


    def __del__(self):
        self.time_master.join()
        if self.launch_monitor:
            self.system_monitor.terminate()
        self.system_controller.terminate()
        self.sc_log.close()
        self.middleware.terminate()
        self.mw_log.close()

    def version(self):
        major = ctypes.c_uint32()
        silkitapi.SilKit_Version_Major(ctypes.byref(major))
        minor = ctypes.c_uint32()
        silkitapi.SilKit_Version_Minor(ctypes.byref(minor))
        patch = ctypes.c_uint32()
        silkitapi.SilKit_Version_Patch(ctypes.byref(patch))
        bn = ctypes.c_uint32()
        silkitapi.SilKit_Version_BuildNumber(ctypes.byref(bn))
        return f"{major.value}.{minor.value}.{patch.value};{bn.value}"
