"""OPS243-C Radar Sensor Servicclass HardwareGPIO:
    """GPIO HAL for Raspberry Pi 5."""

    def __init__(self, pin: int):
        self.pin = pin
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        self.GPIO.setmode(GPIO.BCM)
        self.GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self._available = TrueniPreSense OPS243-C connected via UART and a host interrupt line wired to a GPIO pin.

This module provides a small, testable service class with a hardware abstraction layer (HAL)
so it can run on a Raspberry Pi (using RPi.GPIO) or in a desktop/dev environment (mocked).

Contract (simple):
- Inputs: serial port path (e.g. '/dev/ttyACM0'), baudrate (default 9600), optional gpio_pin for host interrupt
- Outputs: emits parsed radar readings via a callback (callable taking one dict)
- Error modes: serial open failure, parse errors, GPIO not available

"""

from __future__ import annotations

import json
import time
import threading
import logging
from typing import Callable, Optional, Dict

try:
    import serial
except Exception:
    serial = None  # serial may be absent in test environments

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


class HardwareGPIO:
    """GPIO HAL for Raspberry Pi 5."""

    def __init__(self, pin: int):
        self.pin = pin
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self._available = True
            LOGGER.info("GPIO hardware access initialized for pin %d", pin)
        except (ImportError, RuntimeError) as e:
            LOGGER.warning(f"GPIO not available: {e}")
            LOGGER.info("Using mock GPIO - hardware functions disabled")
            self._available = False
            
            # Mock GPIO for environments without GPIO access
            class MockGPIO:
                BCM = "BCM"
                IN = "IN"
                PUD_DOWN = "PUD_DOWN"
                RISING = "RISING"
                def setmode(self, mode): pass
                def setup(self, pin, mode, pull_up_down=None): pass
                def add_event_detect(self, pin, edge, callback=None): pass
            
            self.GPIO = MockGPIO()

    def add_event_detect(self, edge, callback: Callable):
        if self._available:
            self.GPIO.add_event_detect(self.pin, edge, callback=callback)
        else:
            LOGGER.debug("GPIO event detection skipped - hardware not available")


class OPS243Service:
    """High-level service for OPS243 radar sensor.

    Methods:
    - start(callback): start background thread reading serial and GPIO interrupts; callback called with parsed dict
    - stop(): stop threads and close serial
    """

    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 9600, gpio_pin: Optional[int] = None):
        self.port = port
        self.baudrate = baudrate
        self.gpio_pin = gpio_pin
        self._serial = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[Dict], None]] = None
        self._gpio_hal: Optional[HardwareGPIO] = None

    def start(self, callback: Callable[[Dict], None]) -> bool:
        """Start the radar service. Returns True on (likely) success.

        The callback will be called for each parsed radar reading as a dict.
        """
        self._callback = callback

        # Open serial
        if serial is None:
            LOGGER.warning("pyserial not available; serial reads will be disabled")
        else:
            try:
                self._serial = serial.Serial(self.port, self.baudrate, timeout=1)
                # Small delay for device readiness
                time.sleep(0.2)
                # Set JSON output if supported by device
                try:
                    self._serial.write(b'OJ\n')
                except Exception:
                    LOGGER.debug("Failed to send OJ command; continuing")
            except Exception as e:
                LOGGER.error(f"Failed to open serial port {self.port}: {e}")
                # continue running in mock mode if needed

        # Setup GPIO if requested
        if self.gpio_pin is not None:
            self._gpio_hal = HardwareGPIO(self.gpio_pin)
            if getattr(self._gpio_hal, '_available', False):
                # Use RPi.GPIO constants
                self._gpio_hal.add_event_detect(self._gpio_hal.GPIO.RISING, self._gpio_callback)
            else:
                # mock: no hardware event; user may call simulate_pulse in tests
                self._gpio_hal.add_event_detect(None, self._gpio_callback)

        # Start background reader thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()
        LOGGER.info("OPS243Service started")
        return True

    def _gpio_callback(self, channel):
        """Handle host interrupt: wake up read loop and process immediately."""
        LOGGER.debug(f"GPIO interrupt on channel {channel}")
        # On interrupt we'll try a quick immediate read
        self._try_read_once()

    def _try_read_once(self):
        if not self._serial:
            return
        try:
            if self._serial.in_waiting > 0:
                line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                parsed = self._parse_line(line)
                if parsed and self._callback:
                    try:
                        self._callback(parsed)
                    except Exception:
                        LOGGER.exception("Callback raised during immediate read")
        except Exception:
            LOGGER.exception("Error during immediate serial read")

    def _reader_loop(self):
        LOGGER.debug("Reader thread running")
        while not self._stop_event.is_set():
            try:
                if self._serial and self._serial.in_waiting > 0:
                    line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                    parsed = self._parse_line(line)
                    if parsed and self._callback:
                        try:
                            self._callback(parsed)
                        except Exception:
                            LOGGER.exception("Callback error in reader loop")
                else:
                    # Sleep briefly to avoid busy loop
                    time.sleep(0.02)
            except Exception:
                LOGGER.exception("Error in reader loop")
                time.sleep(0.5)

    def _parse_line(self, line: str) -> Optional[Dict]:
        if not line:
            return None
        # Attempt JSON parse
        try:
            if line.startswith('{'):
                data = json.loads(line)
                data['_raw'] = line
                data['_ts'] = time.time()
                return data
        except Exception:
            LOGGER.debug("Failed JSON parse for line")

        # Fallback: try to split "<speed> <unit>" or "MAG:<mag> SPD:<spd>"
        parts = line.split()
        if len(parts) >= 2:
            try:
                speed = float(parts[0])
                unit = parts[1]
                return {'speed': speed, 'unit': unit, '_raw': line, '_ts': time.time()}
            except Exception:
                pass

        # Unknown format
        LOGGER.debug(f"Unrecognized radar line: {line}")
        return {'_raw': line, '_ts': time.time()}

    def stop(self):
        LOGGER.info("Stopping OPS243Service")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
        except Exception:
            LOGGER.debug("Error closing serial")


if __name__ == '__main__':
    # Simple demo when run standalone
    logging.basicConfig(level=logging.DEBUG)

    def print_cb(d):
        print('RADAR:', d)

    svc = OPS243Service(port='/dev/ttyACM0', baudrate=9600, gpio_pin=None)
    svc.start(print_cb)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        svc.stop()
