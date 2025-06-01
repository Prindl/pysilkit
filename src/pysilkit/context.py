import collections
import ctypes
import time

class SilKitContext(object):
    def __init__(
        self,
        rx_queue_size = 2000
    ):
        self.rx_queue = collections.deque(maxlen=rx_queue_size)
        self.state = None
        self.error_state = None
        self.start_time = time.perf_counter()

    def to_ctypes(self):
        return ctypes.py_object(self)
