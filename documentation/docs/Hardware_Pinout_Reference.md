# Hardware Pinout Reference

**Document Version:** 1.0  
**Last Updated:** September 21, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  

## OPS243-C Radar Sensor to Raspberry Pi 5 Pinout

This document provides the complete pinout reference for connecting the OmniPreSense OPS243-C radar sensor to the Raspberry Pi 5 GPIO header.

### Complete Connection Table

| OPS243 Pin | Function | Wire Color | RPi Physical Pin | RPi GPIO | Description |
|------------|----------|------------|------------------|----------|-------------|
| Pin 3 | Host Interrupt | Orange | Pin 16 | GPIO23 | Real-time detection signal (active low) |
| Pin 4 | Reset | Yellow | Pin 18 | GPIO24 | Software reset control (active low) |
| Pin 6 | UART RxD | Green | Pin 8 | GPIO14 (TXD) | Radar receives commands |
| Pin 7 | UART TxD | White | Pin 10 | GPIO15 (RXD) | Radar transmits data |
| Pin 9 | 5V Power | Red | Pin 4 | 5V Power | Power supply (150mA typical) |
| Pin 10 | Ground | Black | Pin 6 | Ground | Common ground |
| **Pin 1** | **Low Alert/Sampling** | **Blue** | **Pin 29** | **GPIO5** | **Speed/range low threshold alert** |
| **Pin 2** | **High Alert** | **Purple** | **Pin 31** | **GPIO6** | **Speed/range high threshold alert** |

### Raspberry Pi 5 GPIO Header Layout

```
     3V3  (1) (2)  5V     ← Pin 4 (Red - Radar Power)
   GPIO2  (3) (4)  5V
   GPIO3  (5) (6)  GND    ← Pin 6 (Black - Radar Ground)
   GPIO4  (7) (8)  GPIO14 ← Pin 8 (Green - Radar RxD)
     GND  (9) (10) GPIO15 ← Pin 10 (White - Radar TxD)
  GPIO17 (11) (12) GPIO18
  GPIO27 (13) (14) GND
  GPIO22 (15) (16) GPIO23 ← Pin 16 (Orange - Radar Interrupt)
     3V3 (17) (18) GPIO24 ← Pin 18 (Yellow - Radar Reset)
  GPIO10 (19) (20) GND
   GPIO9 (21) (22) GPIO25
  GPIO11 (23) (24) GPIO8
     GND (25) (26) GPIO7
   GPIO0 (27) (28) GPIO1
   GPIO5 (29) (30) GND    ← Pin 29 (Blue - Radar Low Alert)
   GPIO6 (31) (32) GPIO12 ← Pin 31 (Purple - Radar High Alert)
  GPIO13 (33) (34) GND
  GPIO19 (35) (36) GPIO16
  GPIO26 (37) (38) GPIO20
     GND (39) (40) GPIO21
```

### Connection Categories

#### Essential Connections (Minimum Required)
These connections are required for basic radar functionality:

- **Power**: Pin 9 (Red) → Pi Pin 4 (5V)
- **Ground**: Pin 10 (Black) → Pi Pin 6 (GND)
- **UART Data**: Pin 6 (Green) → Pi Pin 8 (GPIO14), Pin 7 (White) → Pi Pin 10 (GPIO15)

#### Enhanced GPIO Integration (Recommended)
These connections enable advanced radar-camera correlation:

- **Host Interrupt**: Pin 3 (Orange) → Pi Pin 16 (GPIO23)
- **Reset Control**: Pin 4 (Yellow) → Pi Pin 18 (GPIO24)
- **Speed Alerts**: Pin 1 (Blue) → Pi Pin 29 (GPIO5), Pin 2 (Purple) → Pi Pin 31 (GPIO6)

### Software Configuration

#### GPIO Pin Assignments in Code

```python
# IMX500 AI Host Capture Service Configuration
RADAR_GPIO_PINS = {
    "host_interrupt": 23,  # Orange wire - Real-time detection
    "reset": 24,           # Yellow wire - Software reset
    "low_alert": 5,        # Blue wire - Low speed/range alerts
    "high_alert": 6        # Purple wire - High speed/range alerts
}
```

#### UART Configuration

```python
# Radar UART Settings
RADAR_UART_PORT = "/dev/ttyACM0"
RADAR_BAUD_RATE = 115200
RADAR_DATA_BITS = 8
RADAR_PARITY = "none"
RADAR_STOP_BITS = 1
```

### GPIO Interrupt Functionality

#### Host Interrupt (GPIO23 - Orange Wire)
- **Purpose**: Real-time detection notification from radar
- **Behavior**: Goes LOW when radar detects an object
- **System Response**: Triggers immediate IMX500 AI capture for perfect correlation
- **Benefits**: Sub-100ms response time, hardware-level event detection

#### Speed Alert Pins (GPIO5/GPIO6 - Blue/Purple Wires)
- **Low Alert (GPIO5)**: Configurable low speed threshold (e.g., 15 mph)
- **High Alert (GPIO6)**: Configurable high speed threshold (e.g., 45 mph)
- **Configuration**: Set via radar API commands `AL<speed>` and `AH<speed>`
- **Use Cases**: Adjust camera behavior based on vehicle speed

#### Reset Control (GPIO24 - Yellow Wire)
- **Purpose**: Software reset of radar sensor
- **Implementation**: Active LOW pulse (1ms minimum)
- **Use Cases**: Recovery from radar lockups, system initialization

### Radar API Commands for GPIO Control

```bash
# Enable GPIO outputs
IG          # Enable host interrupt output
AL15        # Set low speed alert to 15 mph
AH45        # Set high speed alert to 45 mph

# Query current settings
?G          # Get GPIO settings
?A          # Get all current settings
```

### Troubleshooting

#### Common Issues

1. **No UART Data**
   - Check UART enable: `sudo raspi-config nonint do_serial 1`
   - Verify baud rate: Default is 9600, system uses 115200
   - Check wiring: Green/White wires must be cross-connected

2. **GPIO Interrupts Not Working**
   - Verify pull-up resistors: `GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)`
   - Check pin permissions: Run service with appropriate privileges
   - Test with `gpio readall` command

3. **Power Issues**
   - Check 5V supply: 150mA minimum for radar
   - Verify ground connection: Pin 10 to Pi Pin 6
   - Monitor voltage: Should be stable 4.75-5.25V

#### Verification Commands

```bash
# Check UART communication
sudo cat /dev/ttyACM0

# Test GPIO status
gpio readall

# Check system logs
sudo journalctl -u imx500-ai-capture -f

# Verify radar configuration
echo "?A" | sudo tee /dev/ttyACM0
```

### Hardware Specifications

#### OPS243-C Radar Sensor
- **Operating Frequency**: 24.125 GHz
- **Detection Range**: 1-100m (vehicles up to 200m)
- **Speed Accuracy**: ±0.5%
- **Beam Pattern**: 20° horizontal × 24° vertical
- **Power Consumption**: 150mA @ 5V typical
- **Interface**: UART (9600-115200 baud), GPIO

#### Raspberry Pi 5 GPIO
- **Voltage Levels**: 3.3V logic (5V tolerant on some pins)
- **Current Capacity**: 16mA per pin maximum
- **Pull-up/Pull-down**: Software configurable
- **Interrupt Capability**: All GPIO pins support edge detection

### Safety Notes

⚠️ **Important Safety Information**

- **Power Off First**: Always power off Pi before making connections
- **Voltage Compatibility**: Radar GPIO outputs are 3.3V compatible
- **Current Limits**: Do not exceed 16mA per GPIO pin
- **ESD Protection**: Use anti-static precautions when handling components
- **Double-Check Connections**: Incorrect wiring can damage components

### Related Documentation

- [Technical Design Document - Hardware Design](./Technical_Design.md#3-hardware-design)
- [Implementation & Deployment Guide - Hardware Assembly](./Implementation_Deployment.md#22-hardware-assembly)
- [User Guide - Hardware Setup Quick Reference](./User_Guide.md#2-hardware-setup-quick-reference)
- [OPS243-C Datasheet](../archive/OPS-DS-003-M_OPS243.pdf)

---

**Document History**
- v1.0 (Sep 21, 2025): Initial pinout documentation with enhanced GPIO integration