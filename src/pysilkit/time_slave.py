import struct
import time

from typing import Optional

from .library import silkitapi
from .utilities import auto_context
from .subscriber import SilKitSubscriber


class SilKitTimeSlave(SilKitSubscriber):
    def __init__(
        self,
        participant,
        name:str,
        *,
        timeout = 5.0
    ):
        self.master_time_since_boot = None
        self.master_boot_date = None
        self.slave_sync_time = None
        self.offset = None
        super(SilKitTimeSlave, self).__init__(
            participant,
            f"TIME_SLAVE_{name}",
            "GLOBAL_SYNC_TIME",
            media_type="application/octet-stream",
            callback=self.on_msg_recv,
            INSTANCE="TIME_SYNC_1S"
        )
        #Wait until synced
        tmp = time.perf_counter()
        while self.slave_sync_time is None:
            if time.perf_counter() - tmp > timeout:
                raise RuntimeError("Did not receive a sync message within the specified timeout.")
            time.sleep(0.1)

    @silkitapi.SilKit_DataMessageHandler_t
    @staticmethod
    @auto_context
    def on_msg_recv(self, subscriber, event):
        #The time slave periodically receives the time from the master
        self.slave_sync_time = time.perf_counter()
        payload = event.contents.data.to_sequence()
        self.master_boot_date, self.master_time_since_boot = struct.unpack("dd", bytes(payload))

    def get_timestamp(self):
        elapsed_local_time = time.perf_counter() - self.slave_sync_time
        return self.master_boot_date + self.master_time_since_boot + elapsed_local_time
