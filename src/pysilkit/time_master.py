import enum
import multiprocessing
import struct
import time
import datetime

from typing import Optional

from .participant import SilKitParticipant

class TimeMasterState(enum.IntEnum):
    ERROR = -1
    INIT = 0
    STARTED = 1
    RUNNING = 2
    EXITED = 3

class SilKitTimeMaster(multiprocessing.Process):
    def __init__(
        self,
        port = 8500,
        *,
        timeout = 5.0
    ):
        super(SilKitTimeMaster, self).__init__(
            group = None,
            target = None,
            name = f"{self.__class__.__name__}Process",
            args = (),
            kwargs = {},
            daemon = False
        )
        self.timeout = timeout
        self.__active = None
        self.state = multiprocessing.Value("b", TimeMasterState.INIT)
        self.port = port
        self.exit_flag = multiprocessing.Value("b", 0)

    def start(self):
        if self.__active is None:
            self.__active = True
            super(SilKitTimeMaster, self).start()
            self.state.value = TimeMasterState.STARTED
            tmp = time.perf_counter()
            while not self.is_running():
                if time.perf_counter() - tmp > self.timeout:
                    self.state.value = TimeMasterState.ERROR
                    self.join()
                    raise RuntimeError("Could not start TimeMaster within timeout")
                time.sleep(0.1)

    def join(self, timeout=None):
        if self.__active:
            self.exit_flag.value = 1
            self.__active = False
            super(SilKitTimeMaster, self).join(timeout)
        elif self.__active is None:
            raise OSError(f"{self.__class__.__name__} not started yet")

    def is_running(self):
        return self.state.value != TimeMasterState.RUNNING

    def run(self):
        self.state.value = TimeMasterState.RUNNING
        time_master = SilKitParticipant("SilKit_TimeMaster", self.port)
        time_master.add_publisher(
            "TIME_MASTER", "GLOBAL_SYNC_TIME", media_type="application/octet-stream", history=True, INSTANCE="TIME_SYNC_1S"
        )
        # The time master periodically send the date when it was first started
        # and the time in seconds since then
        boot_timestamp = time.perf_counter()
        boot_date = datetime.datetime.now(datetime.timezone.utc).timestamp()
        while self.exit_flag.value == 0:
            time_since_boot = time.perf_counter() - boot_timestamp
            data = struct.pack("dd", boot_date, time_since_boot)
            time_master.publisher("TIME_MASTER").publish(data)
            time.sleep(1)
        self.state.value = TimeMasterState.EXITED
