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

## DHT22 Weather Sensor to Raspberry Pi 5 Pinout

This section documents the connection for the DHT22 temperature and humidity sensor used for environmental monitoring.

### DHT22 Connection Table

| DHT22 Pin | Function | Wire Color | RPi Physical Pin | RPi GPIO | Description |
|-----------|----------|------------|------------------|----------|-------------|
| Pin 1 (VCC) | Power | Red | Pin 2 | 5V Power | Power supply (5V recommended for optimal performance) |
| Pin 2 (Data) | Data Line | Yellow/White | Pin 7 | GPIO4 | Bi-directional data communication |
| Pin 3 (NC) | Not Connected | - | - | - | Not used |
| Pin 4 (GND) | Ground | Black | Pin 6 | Ground | Common ground |

**Note:** DHT22 operates on 3.3V-6V range, but **5V is strongly recommended** for:
- Better signal strength and timing reliability
- Improved noise immunity
- Reduced communication errors and checksum failures

### Raspberry Pi 5 GPIO Header Layout

```
     3V3  (1) (2)  5V     ← Pin 2 (Red - DHT22 Power), Pin 4 (Red - Radar Power)
   GPIO2  (3) (4)  5V
   GPIO3  (5) (6)  GND    ← Pin 6 (Black - DHT22/Radar Ground)
   GPIO4  (7) (8)  GPIO14 ← Pin 7 (Yellow - DHT22 Data), Pin 8 (Green - Radar RxD)
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

#### DHT22 Weather Sensor Integration
These connections enable environmental monitoring with temperature and humidity data:

- **Power**: DHT22 VCC (Red) → Pi Pin 2 (5V) - **Upgraded from 3.3V for improved reliability**
- **Data**: DHT22 Data (Yellow/White) → Pi Pin 7 (GPIO4)
- **Ground**: DHT22 GND (Black) → Pi Pin 6 (GND)

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

# DHT22 Weather Sensor Configuration
DHT22_GPIO_PIN = 4         # Yellow/White wire - Data communication
DHT22_UPDATE_INTERVAL = 600  # Read every 10 minutes
DHT22_POWER_VOLTAGE = "5V"   # Connected to Pin 2 (5V) for optimal performance
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

4. **DHT22 Weather Sensor Issues**
   - **No Temperature/Humidity Data**: Check DHT22 power on Pin 2 (5V) and data on GPIO4
   - **Timing/Checksum Errors**: Ensure 5V power supply (3.3V causes reliability issues)
   - **Intermittent Readings**: Check wiring connections, sensor may need 2-second delay between reads
   - **Invalid Readings**: Verify sensor range (-40°C to 80°C, 0-100% humidity)

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

# Test DHT22 sensor
docker logs dht22-weather --tail=20

# Check DHT22 API endpoint
curl http://localhost:5000/api/weather/dht22

# Test DHT22 GPIO communication
python3 test_dht22_detailed.py
```

### Hardware Specifications

#### OPS243-C Radar Sensor
- **Operating Frequency**: 24.125 GHz
- **Detection Range**: 1-100m (vehicles up to 200m)
- **Speed Accuracy**: ±0.5%
- **Beam Pattern**: 20° horizontal × 24° vertical
- **Power Consumption**: 150mA @ 5V typical
- **Interface**: UART (9600-115200 baud), GPIO

#### DHT22 Weather Sensor

- **Operating Voltage**: 3.3V-6V DC (5V recommended for optimal performance)
- **Temperature Range**: -40°C to +80°C (±0.5°C accuracy)
- **Humidity Range**: 0-100% RH (±2-5% accuracy)
- **Resolution**: 0.1°C temperature, 0.1% humidity
- **Response Time**: <10 seconds
- **Power Consumption**: 1-1.5mA during measurement, 40-50µA standby
- **Interface**: Single-wire digital (GPIO4)
- **Update Interval**: 10 minutes (configurable)

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
- v1.1 (Sep 21, 2025): Added DHT22 weather sensor pinout documentation with 5V power upgrade