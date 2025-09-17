"""Unit tests for OPS243Service"""

import time
import threading

from edge_processing.ops243_radar_service import OPS243Service


class FakeSerial:
    def __init__(self, lines):
        self._lines = list(lines)
        self.in_waiting = len(self._lines) > 0
        self.is_open = True

    def readline(self):
        if not self._lines:
            self.in_waiting = 0
            time.sleep(0.01)
            return b''
        line = self._lines.pop(0)
        self.in_waiting = len(self._lines) > 0
        return (line + "\n").encode('utf-8')

    def close(self):
        self.is_open = False

    def write(self, data):
        # ignore
        pass


def test_json_line():
    received = []

    def cb(d):
        received.append(d)

    fake = FakeSerial(['{"speed": 12.3, "units": "mps"}'])

    # patch serial.Serial to return our fake
    import edge_processing.ops243_radar_service as mod
    class SerialFactory:
        pass
    mod.serial = SerialFactory
    mod.serial.Serial = lambda *a, **k: fake

    svc = OPS243Service(port='/dev/fake', baudrate=9600, gpio_pin=None)
    svc.start(cb)

    # wait for reader to pick up
    time.sleep(0.1)
    svc.stop()

    assert len(received) >= 1
    assert 'speed' in received[0]


def test_unrecognized_line():
    received = []

    def cb(d):
        received.append(d)

    fake = FakeSerial(['SOMETHING_UNKNOWN'])

    import edge_processing.ops243_radar_service as mod
    mod.serial = type('S', (), {'Serial': lambda *a, **k: fake})

    svc = OPS243Service(port='/dev/fake', baudrate=9600, gpio_pin=None)
    svc.start(cb)
    time.sleep(0.1)
    svc.stop()

    assert len(received) >= 1
    # Should include _raw key for unknown format
    assert '_raw' in received[0]
