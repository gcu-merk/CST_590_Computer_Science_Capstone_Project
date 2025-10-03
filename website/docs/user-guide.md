# User Guide

---

## Cover Page

**Raspberry Pi 5 Edge ML Traffic Monitoring System**

**User Guide**

![System Logo](../archive/LocalUI.jpg)

**Version 1.2**

---

## Title Page

**Raspberry Pi 5 Edge ML Traffic Monitoring System**

**User Guide**

**Document Version:** 1.2  
**Publication Date:** December 11, 2025  
**Project:** Raspberry Pi 5 Edge ML Traffic Monitoring System  
**Authors:** Documentation Team  

---

## Copyright Page

**Copyright Notice**

© 2025 gcu-merk. All rights reserved.

This document and the software it describes are protected by copyright laws and international treaties. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of the copyright holder.

**Trademarks**

- Raspberry Pi is a trademark of Raspberry Pi Ltd.
- Sony IMX500 is a trademark of Sony Corporation
- All other trademarks are the property of their respective owners.

**Disclaimer**

The information in this document is provided "as is" without warranty of any kind. While every effort has been made to ensure accuracy, the authors assume no responsibility for errors or omissions, or for damages resulting from the use of the information contained herein.

**License**

This project is licensed under the terms specified in the LICENSE file in the project repository.

---

## Preface

### Purpose

This User Guide provides comprehensive instructions for installing, configuring, operating, and maintaining the Raspberry Pi 5 Edge ML Traffic Monitoring System. It is designed to serve both technical operators and non-technical users who need to interact with the system.

**What You Will Learn:**

- How to set up and configure your traffic monitoring system
- How to access and navigate the web dashboard
- How to interpret vehicle detection data and analytics
- How to troubleshoot common problems
- How to maintain your system for optimal performance

### Audience

This guide is intended for:

- **System Operators:** Personnel responsible for installing and maintaining the hardware and software
- **Traffic Analysts:** Users who monitor traffic data and generate reports
- **System Administrators:** IT professionals managing system configuration and cloud integration
- **End Users:** Anyone who needs to access traffic monitoring data through the dashboard
- **Decision Makers:** Managers and officials who review traffic data for planning purposes

**No Advanced Technical Knowledge Required:** This guide is written in plain language with step-by-step instructions that anyone can follow.

### Document Organization

This guide is organized into the following major sections:

1. **General Information:** Overview of what the system does and who can use it
2. **System Summary:** Description of the hardware and software components (simplified)
3. **Getting Started:** How to set up your system for the first time
4. **Using the System:** How to use the dashboard and view traffic data
5. **Troubleshooting:** Solutions to common problems
6. **FAQ:** Answers to frequently asked questions
7. **Help and Contact Details:** How to get additional support
8. **Glossary:** Simple explanations of technical terms

### Prerequisites

**For All Users:**
- Ability to use a web browser (Chrome, Firefox, Safari, Edge)
- Basic understanding of traffic monitoring concepts (vehicle types, speed limits)

**For Technical Operators Only:**
- Familiarity with computer setup and installation procedures
- Basic networking knowledge (how to find IP addresses)
- Comfort following step-by-step instructions

**What You Don't Need:**
- Programming or coding experience
- Advanced computer science knowledge
- Experience with Linux or command-line interfaces (unless performing installation)

### Conventions Used in This Guide

**Text Formatting:**
- **Bold text** indicates buttons, menu items, or important terms you'll see on screen
- `Monospace text` indicates code, web addresses, or command-line text
- *Italic text* indicates emphasis or new concepts

**Icons and Symbols:**
- ⚠️ **WARNING:** Critical information about safety or data loss
- ⚡ **CAUTION:** Important information that could affect system operation
- 💡 **TIP:** Helpful suggestions to make your work easier
- ℹ️ **NOTE:** Additional information or context
- ✅ **SUCCESS:** Indication that a step completed correctly
- ❌ **ERROR:** Common error message or problem

**Step-by-Step Instructions:**
Steps are numbered and include clear actions:

1. **First Action** - Description of what to do
2. **Second Action** - Description of what to do
3. **Third Action** - Description of what to do

**Visual Aids:**
- Screenshots show you exactly what to expect on your screen
- Diagrams illustrate hardware connections and system architecture
- Tables organize information for easy reference
- Highlighted areas in images draw attention to important elements

### Accessibility Features

This guide has been designed with accessibility in mind:

**For Users with Low Vision:**
- High-contrast text and images
- Large, readable fonts (minimum 12pt)
- All images include descriptive alt text
- Dashboard supports browser zoom (up to 200%)
- Screen reader compatible

**For Color-Blind Users:**
- Information is not conveyed by color alone
- Text labels accompany all color-coded indicators
- Patterns and symbols supplement color coding
- Dashboard uses color-blind friendly palettes

**For Keyboard-Only Users:**
- All dashboard functions accessible via keyboard
- Tab navigation supported throughout interface
- Keyboard shortcuts documented for common actions

**For Screen Reader Users:**
- Proper heading hierarchy for navigation
- Descriptive link text (no "click here" links)
- Form labels and ARIA attributes included
- Tables properly marked up with headers

---

## Table of Contents

1. [General Information](#1-general-information)
   - 1.1 [System Features Overview](#11-system-features-overview)
   - 1.2 [Key Capabilities](#12-key-capabilities)
   - 1.3 [User Roles](#13-user-roles)
   - 1.4 [Accessibility & Safety](#14-accessibility--safety)
2. [System Summary](#2-system-summary)
   - 2.1 [Hardware Components](#21-hardware-components)
   - 2.2 [Software Architecture](#22-software-architecture)
   - 2.3 [System Requirements](#23-system-requirements)
3. [Getting Started](#3-getting-started)
   - 3.1 [Hardware Setup Quick Reference](#31-hardware-setup-quick-reference)
   - 3.2 [Initial Configuration](#32-initial-configuration)
   - 3.3 [Accessing the Dashboard](#33-accessing-the-dashboard)
4. [Using the System](#4-using-the-system)
   - 4.1 [Web Dashboard](#41-web-dashboard)
   - 4.2 [Accessing the Dashboard](#42-accessing-the-dashboard)
   - 4.3 [Monitoring Real-Time Traffic](#43-monitoring-real-time-traffic)
   - 4.4 [Using Live Events Feed](#44-using-live-events-feed)
   - 4.5 [Viewing System Logs](#45-viewing-system-logs)
   - 4.6 [Mobile Access](#46-mobile-access)
   - 4.7 [Common Use Cases](#47-common-use-cases)
5. [Troubleshooting](#5-troubleshooting)
   - 5.1 [Common Issues](#51-common-issues)
   - 5.2 [Radar Detection Problems](#52-radar-detection-problems)
   - 5.3 [Dashboard Issues](#53-dashboard-issues)
   - 5.4 [Network Connectivity](#54-network-connectivity)
   - 5.5 [Performance Monitoring](#55-performance-monitoring)
6. [FAQ](#6-faq)
   - 6.1 [General Questions](#61-general-questions)
   - 6.2 [Technical Questions](#62-technical-questions)
   - 6.3 [Troubleshooting Questions](#63-troubleshooting-questions)
7. [Help and Contact Details](#7-help-and-contact-details)
   - 7.1 [Support Channels](#71-support-channels)
   - 7.2 [Additional Resources](#72-additional-resources)
   - 7.3 [Reporting Issues](#73-reporting-issues)
8. [Glossary](#8-glossary)

**Related Documentation:**

- [Technical Design Document](./Technical_Design.md)
- [Implementation & Deployment Guide](./Implementation_Deployment.md)
- [Project Management Summary](./Project_Management.md)
- [References & Appendices](./References_Appendices.md)

---

## 1. General Information

### 1.1 System Features Overview

The Raspberry Pi 5 Edge ML Traffic Monitoring System provides real-time vehicle detection, classification, speed measurement, and traffic analytics at the edge. The system leverages radar-triggered edge AI processing using the Sony IMX500 camera's built-in neural processing unit for on-camera vehicle classification. This advanced approach provides intelligent, power-efficient traffic monitoring with minimal latency and enhanced accuracy.

**For technical details on the ML/AI workflow and component status, see the [ML/AI Workflow and Component Status](./Technical_Design.md#31-mlai-workflow-and-component-status) section in the Technical Design Document.**

### 1.2 Key Capabilities

The system offers the following key features:

- **Radar-Triggered Edge AI:** Combines OPS243-C radar detection with IMX500 on-camera AI processing
- **Real-time Vehicle Classification:** 85-95% accuracy for vehicle type identification  
- **Ultra-Low Latency:** <350ms from detection to classification
- **Power Efficient:** 4-6W average power consumption
- **Multi-Sensor Fusion:** Correlates radar speed/direction with AI vehicle identification
- **Privacy-First:** All AI processing happens locally on the camera sensor
- **Weather Independent:** Radar detection works in all weather conditions
- **Web Dashboard:** GitHub Pages-hosted interface for remote monitoring via Tailscale VPN
- **REST and WebSocket APIs:** For integration and real-time event streaming
- **Real-Time Monitoring:** View live vehicle detections, speed data, and system events

### 1.3 User Roles

The system supports different user roles:

- **Operator:** Installs, configures, and maintains the system on-site. Responsible for hardware setup and basic troubleshooting.
- **Traffic Analyst:** Reviews real-time and historical data via the web dashboard and identifies traffic patterns.
- **Administrator:** Manages system configuration and performs system maintenance tasks.
- **Viewer:** Anyone with access to the dashboard can view real-time traffic data and reports.

### 1.4 Accessibility & Safety

#### Accessibility Features

This system and documentation have been designed to be accessible to all users:

**For Users with Low Vision:**

- High-contrast text and images throughout the documentation and dashboard
- Large, readable fonts (minimum 12pt in documentation, 14px in dashboard)
- All images include descriptive alt text for screen readers
- Dashboard supports browser zoom up to 200% without breaking layout
- Adjustable font sizes in dashboard settings

**For Color-Blind Users:**

- Information is never conveyed by color alone
- Text labels accompany all color-coded indicators
- Patterns and symbols supplement color coding
- Dashboard uses color-blind friendly palettes (tested with deuteranopia and protanopia simulators)
- Status indicators use shapes in addition to colors (circles, squares, triangles)

**For Keyboard-Only Users:**

- All dashboard functions accessible via keyboard navigation
- Tab key moves through all interactive elements in logical order
- Enter and Space keys activate buttons and links
- Escape key closes menus and dialogs
- Keyboard shortcuts available for common actions (press **?** in dashboard to view)

**For Screen Reader Users:**

- Proper heading hierarchy for easy navigation
- Descriptive link text (no "click here" or "read more" links)
- Form labels and ARIA attributes properly implemented
- Tables properly marked up with headers and captions
- Real-time updates announced to screen readers

#### Safety Information

⚠️ **IMPORTANT SAFETY WARNINGS**

Please read and follow these safety guidelines to prevent injury and equipment damage:

**Electrical Safety:**

1. **Use Only Approved Power Supplies**
   - Use only the official Raspberry Pi 5.1V 5A power supply
   - Or use a certified PoE+ (Power over Ethernet) HAT
   - ⚡ **DANGER:** Using incorrect power supplies can cause fire or electric shock

2. **Keep Electronics Dry**
   - Never expose the Raspberry Pi or camera to water or moisture
   - Use only IP65-rated weatherproof enclosures for outdoor installations
   - Ensure all cable entry points are properly sealed
   - ⚡ **DANGER:** Water can cause electric shock and permanent equipment damage

3. **Proper Grounding**
   - Ensure all equipment is properly grounded according to local electrical codes
   - Use surge protectors for outdoor installations
   - Install lightning protection if required by local codes

**Installation Safety:**

1. **Power Off Before Installation**
   - Always disconnect power before connecting or disconnecting components
   - Wait 30 seconds after disconnecting power before touching components
   - ⚡ **DANGER:** Components may remain energized even after power is disconnected

2. **Work at Safe Heights**
   - Use proper ladders or lifts when installing equipment above ground level
   - Wear appropriate personal protective equipment (hard hat, gloves, safety glasses)
   - Have a second person assist with elevated installations
   - ⚡ **DANGER:** Falls from height can cause serious injury or death

3. **Traffic Safety**
   - If installing near roadways, follow all traffic safety regulations
   - Use proper signage, cones, and barriers to protect work area
   - Wear high-visibility clothing
   - Follow local traffic control requirements
   - ⚡ **DANGER:** Working near traffic can result in serious injury or death

**Radar Safety:**

1. **Avoid Prolonged Exposure**
   - The OPS243-C radar operates at 24.125 GHz
   - While low-power, avoid placing your head or body directly in front of radar beam for extended periods
   - Maintain at least 1 foot (30 cm) distance from radar sensor during operation
   - ℹ️ **NOTE:** Radar power level is very low and complies with FCC regulations

2. **Medical Device Interference**
   - Consult your doctor if you have a pacemaker or other implanted medical device
   - Maintain distance from radar during operation if you have medical concerns

**Data Privacy and Legal Compliance:**

1. **Respect Privacy Laws**
   - Ensure your installation complies with local privacy and surveillance laws
   - Post appropriate signage if required by local regulations
   - Do not capture images or video of private property without permission
   - Configure data retention policies according to legal requirements

2. **Secure Your Data**
   - Change default passwords immediately after installation
   - Use strong, unique passwords for all accounts
   - Enable HTTPS/TLS encryption for remote access
   - Keep software updated with security patches

3. **Obtain Required Permits**
   - Check with local authorities for required permits before installation
   - Comply with all zoning and installation regulations
   - Obtain permission before installing on property you don't own

**Environmental Considerations:**

1. **Operating Temperature**
   - Operate only within temperature range: 0°C to 50°C (32°F to 122°F)
   - Use outdoor-rated enclosures with proper ventilation
   - Avoid direct sunlight on enclosure (use shade or reflective coating)

2. **Storage Temperature**
   - Store equipment at -20°C to 70°C (-4°F to 158°F)
   - Protect from moisture, dust, and extreme conditions

3. **Humidity**
   - Operate only in 10% to 90% relative humidity (non-condensing)
   - Use desiccants in outdoor enclosures if necessary

**Maintenance Safety:**

1. **Regular Inspections**
   - Inspect power cables for damage monthly
   - Check weatherproof seals for deterioration
   - Verify mounting hardware is secure
   - Look for signs of overheating or damage

2. **Safe Cleaning**
   - Power off before cleaning any components
   - Use only dry or slightly damp microfiber cloth for camera lens
   - Never use solvents, alcohol, or abrasive cleaners
   - Allow equipment to dry completely before powering on

**Emergency Procedures:**

**If You Smell Burning or See Smoke:**

1. Immediately disconnect power at the source
2. Do not touch hot components
3. Use appropriate fire extinguisher if fire is present (Class C for electrical fires)
4. Evacuate area and call emergency services if fire cannot be controlled
5. Do not attempt to salvage equipment until safe to do so

**If Equipment Gets Wet:**

1. Immediately disconnect power
2. Do not attempt to power on wet equipment
3. Allow equipment to dry completely (24-48 hours)
4. Have equipment inspected by qualified technician before use
5. Replace equipment if extensive water damage occurred

**If Someone Receives Electric Shock:**

1. Do not touch the person if still in contact with power source
2. Disconnect power immediately
3. Call emergency services (911 or local emergency number)
4. Begin CPR if trained and necessary
5. Stay with person until help arrives

**Emergency Contact Information:**

- **Emergency Services:** 911 (or local emergency number)
- **Electrical Safety:** Contact licensed electrician
- **Product Support:** See [Help and Contact Details](#7-help-and-contact-details) section
- **Poison Control:** 1-800-222-1222 (US)

**Regulatory Compliance:**

This equipment must be installed and operated in compliance with:

- FCC Part 15 (Radio Frequency Devices) - United States
- CE Marking requirements - European Union
- Local electrical codes and standards
- Privacy and surveillance regulations
- Traffic monitoring and enforcement laws

⚠️ **Failure to comply with these safety requirements may result in injury, death, equipment damage, legal liability, or regulatory violations.**

💡 **When in Doubt:** If you are unsure about any aspect of installation or operation, consult a qualified professional. Safety is always the top priority.

---

## 2. System Summary

### 2.1 Hardware Components

The system consists of the following hardware components:

#### Core Components

| Component | Model/Specification | Purpose |
|-----------|-------------------|---------|
| **Single Board Computer** | Raspberry Pi 5 (8GB RAM) | Main processing unit |
| **AI Camera** | Sony IMX500 (12MP) | On-chip AI vehicle classification |
| **Radar Sensor** | OPS243-C FMCW Radar | Speed and direction detection (200m range) |
| **External Storage** | Samsung T7 Shield 2TB SSD | Local data storage via USB 3.2 |
| **Power Supply** | Official 5.1V 5A PSU or PoE+ HAT | System power |

#### Connectivity

- **CSI-2 Ribbon Cable:** Connects IMX500 camera to Raspberry Pi
- **GPIO Pins:** Radar sensor connections (UART + GPIO)
- **Ethernet/WiFi:** Network connectivity
- **USB 3.2:** External SSD connection

#### Optional Components

- **Weatherproof Enclosure:** IP65-rated for outdoor installation
- **Mounting Hardware:** Brackets and poles for positioning
- **UPS (Uninterruptible Power Supply):** Backup power during outages

### 2.2 Software Architecture

The system uses a containerized microservices architecture with the following key components:

#### Services

The system uses a containerized microservices architecture with Docker Compose:

- **Redis:** In-memory data store for real-time event streaming and caching
- **Traffic Monitor (API Gateway):** RESTful API and health monitoring endpoints (port 5000)
- **Radar Service:** Interfaces with OPS243-C radar sensor via UART (/dev/ttyAMA0)
- **Data Maintenance:** Automated cleanup of old data and storage management
- **Airport Weather:** Fetches weather data from nearby airports via API
- **DHT22 Weather:** Reads local temperature and humidity from DHT22 sensor (GPIO pin 4)
- **IMX500 Camera Service:** Runs as host service (not containerized) for direct hardware access

ℹ️ **NOTE:** The IMX500 AI camera service runs directly on the host (Raspberry Pi) rather than in a Docker container because it requires direct access to the camera hardware (`/dev/video*` devices). This is a Raspberry Pi 5-specific requirement.

#### Technology Stack

- **Operating System:** Raspberry Pi OS (64-bit)
- **Containerization:** Docker and Docker Compose
- **Programming Languages:** Python 3.x, JavaScript
- **Database:** SQLite, Redis
- **Web Framework:** Flask (Python), HTML5/CSS3/JavaScript
- **APIs:** REST, WebSocket (Socket.IO)

### 2.3 System Requirements

#### Minimum Hardware Requirements

- Raspberry Pi 5 with 4GB RAM (8GB recommended)
- 32GB microSD card for OS (64GB+ recommended)
- External USB SSD (256GB minimum, 1TB+ recommended for extended storage)
- Compatible IMX500 camera module
- OPS243-C radar sensor with cables
- 5.1V 5A power supply or PoE+ HAT

#### Network Requirements

- Ethernet or WiFi connectivity (1 Mbps minimum for cloud features)
- Static IP address or DHCP reservation (recommended)
- Open ports: 5000 (HTTP), 8080 (API), 443 (HTTPS optional)
- Optional: Tailscale VPN for secure remote access

#### Software Requirements

- Raspberry Pi OS (64-bit, Bullseye or newer)
- Docker Engine 20.x or newer
- Docker Compose v2.x or newer
- Python 3.9 or newer
- Git for version control

#### Environmental Requirements

- **Operating Temperature:** 0°C to 50°C (outdoor enclosure)
- **Storage Temperature:** -20°C to 70°C
- **Humidity:** 10% to 90% non-condensing
- **Installation:** Outdoor-rated IP65 enclosure for harsh environments

---

## 3. Getting Started

### 3.1 Hardware Setup Quick Reference

This section provides a quick reference for the hardware connections. For detailed installation instructions, see the [Implementation & Deployment Guide](./Implementation_Deployment.md).

#### OPS243-C Radar Sensor Pinout

| OPS243 Pin | Function | Wire Color | RPi Physical Pin | RPi GPIO | Notes |
|------------|----------|------------|------------------|----------|-------|
| Pin 3 | Host Interrupt | Orange | Pin 16 | GPIO23 | Real-time detection |
| Pin 4 | Reset | Yellow | Pin 18 | GPIO24 | Software reset |
| Pin 6 | UART RxD | Green | Pin 8 | GPIO14 (TXD) | Commands to radar |
| Pin 7 | UART TxD | White | Pin 10 | GPIO15 (RXD) | Data from radar |
| Pin 9 | 5V Power | Red | Pin 4 | 5V Power | 150mA typical |
| Pin 10 | Ground | Black | Pin 6 | Ground | Common ground |
| **Pin 1** | **Low Alert** | **Blue** | **Pin 29** | **GPIO5** | **Speed/range alerts** |
| **Pin 2** | **High Alert** | **Purple** | **Pin 31** | **GPIO6** | **Speed/range alerts** |

### Key Hardware Features

- **IMX500 AI Camera**: 12MP sensor with on-chip AI processing (CSI-2 ribbon cable)
- **OPS243-C Radar**: 24.125 GHz FMCW radar with 200m range (GPIO + UART)
- **External SSD**: Samsung T7 Shield 2TB for local storage (USB 3.2)
- **Power**: 5.1V 5A official PSU or PoE+ HAT

### Connection Verification

```bash
# Test camera
libcamera-hello --preview=none --timeout=5000

# Test radar UART
sudo cat /dev/ttyACM0

# Check GPIO status
gpio readall
```

For complete installation instructions, hardware assembly, and troubleshooting, see:

- [Technical Design Document - Hardware Design](./Technical_Design.md#3-hardware-design)
- [Implementation & Deployment Guide - Hardware Assembly](./Implementation_Deployment.md#22-hardware-assembly)

### 3.2 Initial Configuration

After completing the hardware setup, follow these steps for initial system configuration:

#### Step 1: Boot and Access the Raspberry Pi

1. Insert the microSD card with Raspberry Pi OS installed
2. Connect power to boot the system
3. Wait 2-3 minutes for initial boot
4. Connect via SSH or direct keyboard/monitor

```bash
# SSH connection (replace with your Pi's IP address on local network)
ssh pi@raspberrypi.local

# Or use direct IP if hostname doesn't work
# Find IP with: hostname -I
```

#### Step 2: Install Required Software

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installations
docker --version
docker compose version
```

#### Step 3: Clone Project Repository

```bash
# Clone the project repository
git clone https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project.git
cd CST_590_Computer_Science_Capstone_Project
```

#### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use nano or your preferred editor)
nano .env

# Set required variables:
# - RADAR_PORT=/dev/ttyAMA0
# - STORAGE_PATH=/mnt/storage
# - API_PORT=5000
```

#### Step 5: Start Services

```bash
# Start all services using Docker Compose
docker compose up -d

# Verify services are running
docker compose ps

# Check service health
docker compose logs
```

#### Step 6: Verify Installation

```bash
# Test camera connection
libcamera-hello --preview=none --timeout=5000

# Test radar UART
sudo cat /dev/ttyAMA0

# Check GPIO status
gpio readall

# Test API endpoint (on Pi itself)
curl http://localhost:5000/api/health/system
```

💡 **Tip:** If you encounter permission errors with GPIO or serial ports, ensure your user is in the `gpio`, `dialout`, and `video` groups.

### 3.3 Accessing the Dashboard

Once the system is configured and running, you can access the web dashboard:

#### Public Access (Recommended)

The easiest way to access the dashboard is through GitHub Pages:

1. **Open any web browser**

2. **Navigate to the public dashboard:**
   ```
   https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/
   ```

3. **The dashboard automatically connects to the API** through Tailscale VPN

💡 **Note:** The GitHub Pages dashboard is publicly accessible, but the API requires Tailscale VPN for security.

#### Local Network Access (Alternative)

If accessing from the same local network as the Raspberry Pi:

1. **Find your Raspberry Pi's IP address:**
   ```bash
   hostname -I
   ```

2. **Access the traffic-monitor API directly:**
   ```
   http://[PI_IP_ADDRESS]:5000
   ```

#### Remote Access via Tailscale

For secure remote access to the API backend:

1. **Install Tailscale on Raspberry Pi** (if not already installed):
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2. **Install Tailscale on your client device** (laptop, phone, etc.)

3. **Access the API through Tailscale:**
   ```
   https://edge-traffic-monitoring.taild46447.ts.net/api
   ```

💡 **Tip:** The GitHub Pages dashboard already uses the Tailscale API, so you only need Tailscale on your device if accessing the API directly.

---

---

## 4. Using the System

### 4.1 Web Dashboard

The web dashboard (hosted on GitHub Pages) provides real-time monitoring and analytics for the traffic monitoring system. It connects to your Raspberry Pi system via Tailscale VPN for secure remote access.

#### Dashboard Layout & Navigation

The dashboard has **four main tabs**:

- **Overview Tab:**
  - Total vehicles detected (24-hour count)
  - Average, minimum, and maximum speeds
  - Last detected vehicle snapshot image
  - Speed violations counter
  - Current weather conditions
  - Traffic volume chart (24H or 7D views)
  - Speed distribution chart

- **Live Events Tab:**
  - Real-time vehicle detection events
  - WebSocket streaming of detections
  - Filterable event feed (all events, vehicles only, speed events, system events)
  - Pause/resume and clear controls

- **System Logs Tab:**
  - Real-time system log messages
  - Filterable by log level (all, errors, warnings, info)
  - Useful for troubleshooting
  - Pause/resume and clear controls

#### Dashboard Screenshots

![Web Dashboard Overview](CloudUI_As_Built_1.jpg)
*Figure 1: Web Dashboard - Overview Tab with Real-Time Metrics*

![Web Dashboard Live Events](CloudUI_As_Built_2.jpg)
*Figure 2: Web Dashboard - Live Events Tab*

![Web Dashboard System Logs](CloudUI_As_Built_3.jpg)
*Figure 3: Web Dashboard - System Logs Tab*

### 4.2 Accessing the Dashboard

#### Step-by-Step: First Time Access

**Step 1: Open the Dashboard**

1. Open your web browser (Chrome, Firefox, Safari, or Edge recommended)
2. Navigate to the GitHub Pages dashboard:
   ```
   https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/
   ```
3. Press **Enter**

**Step 2: Configure API Connection**

1. When you first open the dashboard, you'll see "API Offline" status indicator
2. Click the **"Configure API"** button (bottom right corner)
3. A configuration modal appears
4. In the "Tailscale Pi IP Address" field, enter your Pi's Tailscale URL:
   ```
   https://edge-traffic-monitoring.taild46447.ts.net/api
   ```
5. Click **"Test Connection"** to verify connectivity
6. If successful, you'll see "✅ Connected successfully"
7. Close the modal

✅ **SUCCESS:** The API status indicator should now show "API Online" with a green dot

💡 **TIP:** Bookmark this page for quick access! Your API configuration is saved in your browser.

**Step 3: View Live Data**

1. Once connected, the dashboard automatically loads recent data
2. You should see:
   - Total vehicle count updating
   - Last detected vehicle snapshot appearing
   - Weather data loading
   - Charts populating with data

### 4.3 Monitoring Real-Time Traffic

#### Overview Tab Features

**Real-Time Metrics Cards:**

1. **Total Vehicles Card** (top left):
   - Shows total vehicles detected in last 24 hours
   - Displays average, minimum, and maximum speeds
   - Updates automatically as new vehicles are detected

2. **Last Detected Card** (top center):
   - Shows the most recent vehicle detection snapshot
   - Displays vehicle type (car, truck, bus, motorcycle)
   - Shows speed of last detected vehicle
   - Image updates when new vehicle is detected (24-hour retention)
   - Status indicator shows "Connecting...", "No recent detections", or timestamp

3. **Speed Violations Card** (top right):
   - Counts vehicles exceeding 25 mph speed limit
   - Shows last 24 hours of violations
   - Scrollable list of recent violations with timestamps and speeds

4. **Weather Card** (bottom):
   - Airport temperature (from CheckWX API)
   - Local temperature (from DHT22 sensor on Pi)
   - Local humidity (from DHT22 sensor)
   - Wind speed and direction (from airport weather)
   - Updates every 5 minutes

**Traffic Volume Chart:**

- Located below the metrics cards
- Shows vehicle detections over time
- Two view modes:
  - **24H** button: Hourly data for last 24 hours
  - **7D** button: Daily totals for last 7 days
- Bar chart format - taller bars = more traffic
- Useful for identifying peak traffic times

**Speed Distribution Chart:**

- Shows histogram of vehicle speeds
- Grouped into speed ranges (buckets)
- Helps identify speeding patterns
- Most vehicles should cluster around posted speed limit

#### Interpreting the Data

**Understanding Confidence Levels:**

Each vehicle detection includes a confidence score:
- **90-100%** = Very confident ✅ (Highly reliable classification)
- **75-89%** = Confident ⚠️ (Generally reliable)
- **60-74%** = Somewhat confident ℹ️ (Less reliable, verify if important)
- **Below 60%** = Low confidence ❌ (May be inaccurate)

**Speed Accuracy:**

- Radar provides highly accurate speed measurements (±1 mph)
- Speed is measured continuously while vehicle is in detection zone
- Reported speed is the average during detection period

**Vehicle Type Classification:**

- AI classification happens on the IMX500 camera's NPU
- Classification accuracy depends on:
  - Lighting conditions (better in daylight)
  - Vehicle distance (best at 20-100 feet)
  - Angle of view (front/rear views work best)
  - Weather conditions (clear weather is best)

### 4.4 Using Live Events Feed

The Live Events tab shows real-time detection events as they happen via WebSocket streaming.

#### Step-by-Step: Viewing Live Events

**Step 1: Navigate to Live Events Tab**

1. Click the **"Live Events"** tab in the navigation bar
2. The events feed loads automatically
3. New events appear at the top of the list in real-time

**Step 2: Understanding Event Entries**

Each event shows:
- **Timestamp:** When the detection occurred
- **Event Type:** Vehicle detection, speed event, or system event
- **Service:** Which system component generated the event
- **Details:** Vehicle type, speed, confidence, or system message

Example event:
```
2025-10-02 14:32:15 | INFO | vehicle-consolidator | 
Car detected at 35 mph (confidence: 95%)
```

**Step 3: Filtering Events**

Use the dropdown filter to view specific event types:
- **All Events:** Shows everything (default)
- **Vehicle Detections:** Only vehicle detection events
- **Speed Events:** Only speed-related events  
- **System Events:** Only system status messages

**Step 4: Controls**

- **Pause Button:** Temporarily stop new events from appearing (useful for reviewing)
- **Resume:** Resume live event streaming
- **Clear Events:** Remove all current events from the display

💡 **TIP:** Pause the feed when you need to read specific events carefully. Don't forget to resume!

### 4.5 Viewing System Logs

The System Logs tab provides technical diagnostic information useful for troubleshooting.

#### When to Use System Logs

Use system logs when:
- Dashboard shows errors or warnings
- Vehicle detections aren't appearing
- Weather data isn't updating
- System seems to be malfunctioning
- You need to report an issue

#### Log Levels Explained

- **ERROR** 🔴: Something went wrong (e.g., sensor failure, database error)
- **WARN** 🟡: Potential issue (e.g., high CPU usage, slow response)
- **INFO** ℹ️: Normal operational messages (e.g., service started, detection processed)

#### Using the Log Filter

1. Click **System Logs** tab
2. Use the dropdown to filter by severity:
   - **All Levels:** See everything
   - **Errors Only:** Only show problems
   - **Warnings+:** Show warnings and errors
   - **Info+:** Show all messages (default)

3. Look for patterns:
   - Repeated errors indicate persistent problem
   - Timestamp shows when issue occurred
   - Service name shows which component has the issue

Example log entry:
```
2025-10-02 14:35:22 | ERROR | radar-service | 
Failed to read from UART device /dev/ttyAMA0
```

💡 **TIP:** If you see errors, note the timestamp and service name when reporting issues.

### 4.6 Mobile Access

The dashboard is fully responsive and works on mobile devices through your phone's web browser - no app installation required!

#### Accessing from Mobile

**Step 1: Open Your Mobile Browser**

1. Open Safari (iPhone/iPad), Chrome, or any modern mobile browser
2. Navigate to the dashboard URL:
   ```
   https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/
   ```
3. The dashboard automatically adapts to your screen size

**Step 2: Add to Home Screen (Optional)**

For quick access, you can add the dashboard to your home screen:

**On iPhone/iPad:**
1. Tap the Share button (square with arrow)
2. Scroll down and tap "Add to Home Screen"
3. Name it "Traffic Monitor" or similar
4. Tap "Add"
5. Icon appears on your home screen like a regular app

**On Android:**
1. Tap the menu button (three dots)
2. Tap "Add to Home screen"
3. Name it and tap "Add"
4. Icon appears on your home screen

**Step 3: Configure API Connection**

1. Tap the "Configure API" button
2. Enter your Tailscale URL (same as desktop)
3. Tap "Test Connection"
4. Once connected, you're ready to use the dashboard

#### Mobile-Friendly Features

The dashboard is optimized for mobile with:
- **Touch-friendly buttons and controls**
- **Responsive layout** that adapts to screen size
- **Swipe-friendly tabs** for easy navigation
- **Readable text** on small screens
- **Efficient data loading** for mobile networks

#### Mobile Usage Tips

💡 **Tips for mobile users:**
- Rotate to landscape for better chart viewing
- Pinch to zoom on charts if needed
- Use Wi-Fi for best performance
- Close other browser tabs to save battery
- Enable browser notifications for real-time alerts (if supported)

### 4.7 Common Use Cases

#### Use Case 1: Live Traffic Monitoring

1. User opens the GitHub Pages dashboard in a browser
2. Views the Overview tab showing real-time metrics:
   - Total vehicles in last 24 hours
   - Last detected vehicle snapshot with speed
   - Speed violations count
   - Current weather conditions
3. Checks the Live Events tab for real-time vehicle detections
4. Reviews traffic volume and speed distribution charts

#### Use Case 2: Reviewing Speed Violations

1. User views the Speed Violations card on Overview tab
2. Sees count of vehicles exceeding 25 mph in last 24 hours
3. Scrolls through list of recent violations with timestamps and speeds
4. Can switch to Live Events tab to see more detailed violation data

#### Use Case 3: Monitoring System Health

1. User clicks on System Logs tab
2. Filters by log level to see errors or warnings
3. Identifies any issues with camera, radar, or other services
4. Notes timestamps and error messages for troubleshooting

---

## 5. Troubleshooting

### 5.1 Common Issues

#### Dashboard Shows "No Data"

**Problem:** Dashboard displays "No data" message when you expect to see vehicle detections.

**Solutions:**

1. **Verify service status:**
   ```bash
   docker compose ps
   # All services should show "running" status
   ```

2. **Check camera and radar connections:**
   ```bash
   # Test camera
   libcamera-hello --preview=none --timeout=5000
   
   # Test radar
   sudo cat /dev/ttyAMA0
   ```

3. **Check database accessibility:**
   ```bash
   # Verify database file exists
   ls -la /mnt/storage/traffic.db
   
   # Check database service logs
   docker logs database-persistence --tail 20
   ```

4. **Review system logs for errors:**
   ```bash
   # Check all service logs
   docker compose logs --tail=50
   ```

#### Vehicle Detections Seem Inaccurate

**Problem:** System is detecting vehicles, but classifications or speeds seem incorrect.

**Solutions:**

1. **Clean the camera lens:**
   - Power off the system
   - Gently clean the IMX500 camera lens with a microfiber cloth
   - Ensure no obstructions block the camera view

2. **Adjust camera angle:**
   - Ensure camera has clear view of roadway
   - Optimal angle is 20-30 degrees from horizontal
   - Avoid backlighting or direct sunlight

3. **Check lighting conditions:**
   - System works best in daylight or good artificial lighting
   - Add external lighting for nighttime operation if needed

4. **Verify radar alignment:**
   - Radar should point directly at traffic flow
   - Check for obstructions blocking radar beam
   - Ensure radar is securely mounted

5. **Review confidence thresholds:**
   ```bash
   # Check current detection settings
   cat config/detection_settings.yaml
   
   # Lower thresholds may increase detections but reduce accuracy
   ```

#### System Running Slowly or Unresponsive

**Problem:** Dashboard is slow to load or system is unresponsive.

**Solutions:**

1. **Check system resources:**
   ```bash
   # Check CPU and memory usage
   top
   
   # Check disk space
   df -h
   ```

2. **Restart services:**
   ```bash
   # Restart all services
   docker compose restart
   
   # Or restart individual service
   docker compose restart radar-service
   ```

3. **Clear old data:**
   ```bash
   # Archive old logs
   mv /mnt/storage/logs/* /mnt/storage/archive/
   
   # Clean up old database records (keep last 30 days)
   python3 scripts/cleanup_old_data.py --days 30
   ```

4. **Check for runaway processes:**
   ```bash
   docker stats
   ```

### 5.2 Radar Detection Problems

#### Radar Service Not Detecting Vehicles

**Problem:** No vehicle detections appearing in radar logs.

**Solutions:**

1. **Check UART connection:**
   ```bash
   # Verify radar device is accessible
   ls -la /dev/ttyAMA0
   
   # Should show device with proper permissions (crw-rw----)
   ```

2. **Add user to dialout group:**
   ```bash
   sudo usermod -aG dialout $USER
   # Log out and back in for changes to take effect
   ```

3. **Verify radar service logs for errors:**
   ```bash
   docker logs radar-service --tail 20
   
   # Look for Redis connection errors or UART issues
   ```

4. **Test radar manually:**
   - Safely walk or drive past the radar sensor
   - Check logs immediately: `docker logs radar-service -f`
   - You should see speed readings

5. **Check radar power:**
   - Verify 5V power is connected to radar sensor
   - Check for loose connections
   - Measure voltage at radar pins if possible

#### Inconsistent Speed Readings

**Problem:** Radar reports erratic or obviously incorrect speeds.

**Solutions:**

1. **Calibrate radar orientation:**
   - Radar works best when aimed directly at traffic flow
   - Angle sensor to minimize ground clutter
   - Secure mounting to prevent vibration

2. **Check for interference:**
   - Move away from other radar sources
   - Ensure no metal objects in radar path
   - Check for EMI from nearby equipment

3. **Verify configuration:**
   ```bash
   # Check radar configuration
   docker exec radar-service cat /config/radar_config.yaml
   ```

4. **Test with known speed reference:**
   - Use GPS speedometer or radar gun
   - Compare readings at various speeds
   - Contact support if consistent offset detected

### 5.3 Dashboard Issues

#### Cannot Access Dashboard

**Problem:** Browser cannot connect to dashboard URL.

**Solutions:**

1. **Try the GitHub Pages dashboard first:**
   ```
   https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/
   ```

2. **If accessing via Tailscale, verify VPN connection:**
   ```bash
   # Check Tailscale status
   tailscale status
   
   # Verify connection to the edge device
   curl https://edge-traffic-monitoring.taild46447.ts.net/health
   ```

3. **For local network access, verify Raspberry Pi is reachable:**
   ```bash
   # On the Pi, check IP address
   hostname -I
   
   # Ping the Pi from your computer (replace with actual IP)
   ping raspberrypi.local
   ```

2. **Check firewall settings:**
   ```bash
   # On the Pi, check if port 5000 is listening
   sudo netstat -tulpn | grep 5000
   
   # Allow port through firewall if needed
   sudo ufw allow 5000/tcp
   ```

3. **Verify API service is running:**
   ```bash
   docker ps | grep api-gateway
   docker logs api-gateway --tail 20
   ```

4. **Try different browser:**
   - Clear browser cache and cookies
   - Try incognito/private browsing mode
   - Test with different browser (Chrome, Firefox, Edge)

#### Dashboard Shows Old Data

**Problem:** Dashboard displays outdated information.

**Solutions:**

1. **Force browser refresh:**
   - Press Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
   - This clears browser cache

2. **Check WebSocket connection:**
   - Open browser developer console (F12)
   - Look for WebSocket connection errors
   - Verify real-time updates are working

3. **Verify data services:**
   ```bash
   # Check traffic-monitor service (API gateway)
   docker logs traffic-monitor --tail 20
   
   # Verify recent data in Redis
   docker exec redis redis-cli XREVRANGE radar_data + - COUNT 5
   ```

4. **Restart API gateway:**
   ```bash
   docker compose restart api-gateway
   ```

### 5.4 Network Connectivity

#### Cannot Connect Remotely via Tailscale

**Problem:** Unable to access dashboard using Tailscale IP.

**Solutions:**

1. **Verify Tailscale is running:**
   ```bash
   # On Raspberry Pi
   sudo tailscale status
   
   # Should show "online" status
   ```

2. **Check Tailscale IP:**
   ```bash
   tailscale ip -4
   # Use this IP to access dashboard
   ```

3. **Restart Tailscale:**
   ```bash
   sudo tailscale down
   sudo tailscale up
   ```

4. **Check ACL rules:**
   - Log into Tailscale admin console
   - Verify device has proper access permissions
   - Check for any blocklisted ports

#### Slow Network Performance

**Problem:** Dashboard loads slowly or data updates are delayed.

**Solutions:**

1. **Test network speed:**
   ```bash
   # Install speedtest-cli if needed
   sudo apt install speedtest-cli
   
   # Run speed test
   speedtest-cli
   ```

2. **Check local network:**
   - Restart router/switch
   - Test with wired Ethernet connection
   - Move closer to WiFi access point

3. **Reduce data polling frequency:**
   - Edit dashboard settings
   - Increase refresh interval from 1s to 5s
   - Reduces network traffic

4. **Optimize database queries:**
   ```bash
   # Vacuum database to improve performance
   docker exec database-persistence sqlite3 /data/traffic.db "VACUUM;"
   ```

### 5.5 Performance Monitoring

#### Monitoring System Performance

**Key Metrics to Monitor:**

- **Detection Rate:** Number of vehicles detected per hour
- **Response Time:** Time from radar detection to dashboard update (<350ms target)
- **Storage Usage:** Disk space used by logs and database
- **Service Uptime:** How long services have been running without restart
- **CPU/Memory Usage:** System resource consumption

#### Performance Monitoring Commands

```bash
# Check service uptime
docker ps --format "table {{.Names}}\t{{.Status}}"

# Monitor storage usage
du -h /mnt/storage/logs/
df -h /mnt/storage

# Check Redis memory usage
docker exec redis redis-cli INFO memory

# View system resources
htop
```

#### Maintenance Tasks

**Daily Checks:**

- Verify dashboard is accessible
- Check recent detections show reasonable vehicle counts
- Monitor system disk space usage
- Review error logs for issues

**Weekly Maintenance:**

- Review radar service logs for errors
- Check that detection data is being properly stored in Redis
- Verify backup systems (if configured)
- Test remote access capabilities

**Monthly Tasks:**

- Update system software: `sudo apt update && sudo apt upgrade`
- Review and archive old log files
- Test emergency procedures and failover systems
- Verify all sensors and hardware connections

---

---

## 6. FAQ

### 6.1 General Questions

**Q: What types of vehicles can the system detect?**

A: The AI camera can detect and classify cars, trucks, motorcycles, and buses. Detection accuracy is highest for standard passenger vehicles (85-95%) and decreases slightly for unusual vehicle types or motorcycles due to their smaller size.

**Q: How accurate is the speed measurement?**

A: The OPS243-C radar sensor provides ±2 mph accuracy for vehicles traveling up to 60 mph under normal conditions. Accuracy may decrease in adverse weather or with very small vehicles (motorcycles, bicycles).

**Q: Can the system work in all weather conditions?**

A: Yes, the system is designed for outdoor use with an IP65-rated enclosure. The radar sensor works reliably in all weather conditions including rain, snow, and fog. Camera-based AI classification may have reduced accuracy in very poor visibility but the radar will continue to detect vehicles and measure speed.

**Q: How much data storage is required?**

A: With default settings, the system generates approximately 1-2 GB of data per day, including logs, detection events, and periodic image captures. The recommended 1TB external SSD provides several months to over a year of storage, depending on traffic volume and retention settings.

**Q: Is the system compliant with privacy regulations?**

A: Yes. All AI processing occurs on the IMX500 camera sensor itself, and the system does not store continuous video footage by default. Only metadata (timestamps, vehicle types, speeds) is logged. The system can be configured to capture snapshots for verification purposes, with appropriate retention policies to comply with local privacy laws.

**Q: Can I integrate this system with existing traffic management systems?**

A: Yes. The system provides REST and WebSocket APIs that can be integrated with external traffic management platforms. See the Technical Design Document for API specifications and integration examples.

### 6.2 Technical Questions

**Q: What network connectivity is required?**

A: The system requires an internet connection for remote access via Tailscale VPN and GitHub Pages dashboard access. The API backend runs locally on the Raspberry Pi but is accessed remotely through Tailscale. Minimum bandwidth requirement is 1 Mbps. For optimal performance, 5-10 Mbps is recommended, especially if the system is capturing and storing snapshots.

**Q: Can I access the system remotely?**

A: Yes. The system supports secure remote access using Tailscale, a mesh VPN that creates a private network between your devices. Tailscale allows you to SSH or access the dashboard from anywhere, as if you were on the same local network. See the Implementation & Deployment Guide for setup instructions.

**Q: How do I connect to the Raspberry Pi using Tailscale?**

A: The system uses Tailscale for secure remote access. After installing Tailscale on both your Raspberry Pi and your client device (laptop/desktop), you can access the system:

**Option 1: Web Dashboard (Recommended)**
```
https://gcu-merk.github.io/CST_590_Computer_Science_Capstone_Project/
```
The GitHub Pages dashboard will automatically connect to your Tailscale-protected API.

**Option 2: Direct API Access**
```bash
# SSH to Raspberry Pi
ssh merk@edge-traffic-monitoring.taild46447.ts.net

# Or access API directly
https://edge-traffic-monitoring.taild46447.ts.net/api
```

Ensure Tailscale is running and connected on both devices. For more details, see the Implementation & Deployment Guide.

**Q: How do I calibrate the speed measurement?**

A: The OPS243-C radar sensor is factory-calibrated and typically requires no additional calibration. However, you can verify accuracy by comparing readings with a GPS speedometer or radar gun. If you notice consistent offsets, check the radar orientation and mounting. Contact support if recalibration is needed.

**Q: What happens if the power goes out?**

A: The system will automatically resume normal operation when power is restored. All services are configured to start on boot. If you have a UPS (Uninterruptible Power Supply), the Raspberry Pi can continue operating for several hours during outages, depending on UPS capacity.

**Q: How do I back up my data?**

A: You can back up data using several methods:

1. **Manual backup:**
   ```bash
   # Copy database to backup location
   cp /mnt/storage/traffic.db /path/to/backup/
   ```

2. **Automated backup script:**
   ```bash
   # Run backup script (if configured)
   ./scripts/backup_data.sh
   ```

3. **Cloud synchronization:** Enable cloud sync in settings to automatically upload data to cloud storage.

**Q: Can I adjust detection sensitivity or thresholds?**

A: Yes, detection thresholds and sensitivity can be adjusted in the configuration files. This allows you to fine-tune the system for your specific deployment:

- **AI Confidence Threshold:** Minimum confidence score for vehicle classification (default: 0.70)
- **Speed Threshold:** Minimum/maximum speed for logging (e.g., ignore stationary objects)
- **ROI (Region of Interest):** Define specific areas of the camera frame to monitor

See the Technical Design Document for detailed configuration parameters.

**Q: How many vehicles can the system handle simultaneously?**

A: The system can reliably process 3-5 vehicles simultaneously in the camera's field of view. The IMX500's on-chip AI can handle multiple detections in a single frame, and the radar can track multiple targets. Performance depends on vehicle spacing and speed.

### 6.3 Troubleshooting Questions

**Q: The dashboard shows "No data" - what should I check?**

A:

1. Verify the camera and radar connections
2. Check that all services are running: `docker compose ps`
3. Ensure the database is accessible: `ls -la /mnt/storage/traffic.db`
4. Look for error messages in the system logs: `docker compose logs --tail=50`

See the [Troubleshooting](#5-troubleshooting) section for detailed solutions.

**Q: How do I update the system software?**

A: Software updates should be performed carefully to avoid disrupting service:

1. **Backup your data first:**
   ```bash
   ./scripts/backup_data.sh
   ```

2. **Pull latest code:**
   ```bash
   git pull origin main
   ```

3. **Rebuild containers:**
   ```bash
   docker compose down
   docker compose build
   docker compose up -d
   ```

4. **Verify services:**
   ```bash
   docker compose ps
   ```

Always backup your data before performing updates. See the Implementation & Deployment Guide for detailed update procedures.

**Q: Why are my vehicle classifications inaccurate?**

A: Inaccurate classifications can result from several factors:

1. **Poor lighting:** Ensure adequate lighting for camera
2. **Camera angle:** Optimize camera position for side or front/rear vehicle views
3. **Dirty lens:** Clean camera lens with microfiber cloth
4. **Wrong ROI:** Adjust region of interest to focus on road area
5. **Low confidence threshold:** Increase threshold to filter low-confidence detections

See [Vehicle Detections Seem Inaccurate](#vehicle-detections-seem-inaccurate) for detailed troubleshooting steps.

**Q: How do I reset the system to factory defaults?**

A: To reset the system:

1. **Backup important data first**
2. **Stop all services:**
   ```bash
   docker compose down
   ```

3. **Remove data volumes:**
   ```bash
   docker volume rm $(docker volume ls -q)
   ```

4. **Restore default configuration:**
   ```bash
   cp config/default_config.yaml config/config.yaml
   ```

5. **Restart services:**
   ```bash
   docker compose up -d
   ```

⚠️ **Warning:** This will delete all historical data and reset all settings.

---

## 7. Help and Contact Details

### 7.1 Support Channels

If you have questions, encounter issues, or need assistance with the Raspberry Pi 5 Edge ML Traffic Monitoring System, please use the following support channels:

#### Documentation Resources

- **Technical Design Document:** [Technical_Design.md](./Technical_Design.md) - Detailed technical specifications and architecture
- **Implementation & Deployment Guide:** [Implementation_Deployment.md](./Implementation_Deployment.md) - Installation and deployment instructions
- **Project Management Summary:** [Project_Management.md](./Project_Management.md) - Project overview and planning documents
- **References & Appendices:** [References_Appendices.md](./References_Appendices.md) - Additional references and resources

#### Online Resources

- **GitHub Repository:** [CST_590_Computer_Science_Capstone_Project](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project)
  - View source code, report issues, and contribute to the project
  - Check the Wiki for additional documentation and tutorials
  - Review closed issues for solutions to common problems

- **Community Forum:** Join discussions with other users and developers (link TBD)
- **Video Tutorials:** Step-by-step video guides for installation and configuration (link TBD)

#### Direct Support

- **Email Support:** Contact the project team at `support@example.com` (replace with actual support email)
- **Issue Tracking:** Report bugs or request features via GitHub Issues
- **Commercial Support:** For enterprise deployments or custom development, contact the project maintainers

### 7.2 Additional Resources

#### Hardware Documentation

- **Raspberry Pi 5 Documentation:** [raspberrypi.com/documentation](https://www.raspberrypi.com/documentation/)
- **Sony IMX500 Camera:** See Technical Design Document for specifications
- **OPS243-C Radar Sensor:** [OmniPreSense Documentation](https://omnipresense.com/product/ops243-doppler-radar-sensor/)

#### Software and Tools

- **Docker Documentation:** [docs.docker.com](https://docs.docker.com/)
- **Python Documentation:** [python.org/doc](https://www.python.org/doc/)
- **Tailscale VPN:** [tailscale.com/kb](https://tailscale.com/kb/)

#### Learning Resources

- **Edge AI and ML:** Resources on edge machine learning and computer vision
- **Traffic Monitoring Best Practices:** Guidelines for traffic monitoring systems
- **IoT and Sensor Networks:** Background on IoT system design

### 7.3 Reporting Issues

When contacting support or reporting an issue, please provide the following information to help us assist you more effectively:

#### Required Information

1. **System Version:**
   ```bash
   cat version.txt
   # Or check git commit hash
   git rev-parse HEAD
   ```

2. **Hardware Configuration:**
   - Raspberry Pi model (Pi 5 8GB, etc.)
   - Camera model (IMX500)
   - Radar sensor (OPS243-C)
   - Storage device type and capacity

3. **Issue Description:**
   - Clear description of the problem
   - What you expected to happen
   - What actually happened
   - When the issue started

4. **Error Messages and Logs:**
   ```bash
   # Collect service logs
   docker compose logs > system_logs.txt
   
   # Check system logs
   journalctl -xe > system_journal.txt
   
   # Include these files with your issue report
   ```

5. **Steps to Reproduce:**
   - Detailed steps to reproduce the problem
   - Frequency (always, intermittent, rare)
   - Any recent changes or updates

6. **Screenshots:**
   - If applicable, include screenshots of dashboard or error messages
   - Use browser developer console (F12) to capture JavaScript errors

#### Bug Report Template

```markdown
**System Version:** [e.g., v1.2, commit abc123]
**Hardware:** [e.g., Raspberry Pi 5 8GB, IMX500, OPS243-C]
**OS:** [e.g., Raspberry Pi OS 64-bit, Bullseye]

**Description:**
[Clear description of the issue]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [And so on...]

**Expected Behavior:**
[What you expected to happen]

**Actual Behavior:**
[What actually happened]

**Error Messages:**
[Paste any error messages or logs]

**Additional Context:**
[Any other relevant information]
```

---

## 8. Glossary

### Core System Terms

**AI Camera (IMX500):** Sony 12MP camera sensor with built-in neural processing unit that performs on-chip vehicle classification

**API Gateway:** Service that provides REST and WebSocket endpoints for external system integration; in this system, the `traffic-monitor` service acts as the API gateway

**Dashboard:** The unified web interface hosted on GitHub Pages for monitoring traffic, viewing analytics, and accessing system logs

**Data Integration:** The process of combining data from multiple sensors (IMX500 camera and OPS243-C radar) into a unified stream for analysis and storage in Redis

**Detection Event:** A recorded instance of a vehicle detection, including timestamp, vehicle type, speed, and location

**Edge AI:** Artificial intelligence processing performed locally on the device (camera sensor) rather than in the cloud

**FMCW Radar:** Frequency-Modulated Continuous Wave radar technology used in the OPS243-C sensor

**Fusion:** The process of combining data from multiple sensors (radar + camera) to create more accurate detections

**GPIO:** General Purpose Input/Output pins on the Raspberry Pi used to interface with sensors

**IMX500:** Sony image sensor with integrated AI processing capabilities

**OPS243-C:** 24.125 GHz Doppler radar sensor for vehicle speed and direction detection

**Redis:** In-memory data store used for real-time event streaming between services

**ROI (Region of Interest):** Specific area of the camera frame designated for vehicle monitoring

**SQLite:** Embedded database used for persistent storage of detection events

**Tailscale:** Mesh VPN service for secure remote access to the system

**UART:** Universal Asynchronous Receiver-Transmitter serial communication protocol used for radar sensor

**WebSocket:** Communication protocol for real-time bidirectional data exchange between server and client

### Technical Terms

**Bounding Box:** Rectangle drawn around detected vehicles in the camera frame

**Classification:** Process of identifying vehicle type (car, truck, motorcycle, bus) using AI

**Confidence Score:** AI certainty level (0-100%) in vehicle classification accuracy

**Container:** Isolated environment for running services using Docker

**Detection Threshold:** Minimum confidence or signal strength required to register a vehicle detection

**Docker Compose:** Tool for defining and running multi-container Docker applications

**Microservices:** Software architecture where system is composed of small, independent services

**Neural Network:** AI model used by IMX500 camera to classify vehicle types

**PoE+ (Power over Ethernet Plus):** Technology that provides power and network connectivity over a single cable

**SSH (Secure Shell):** Protocol for secure remote command-line access to the Raspberry Pi

**UPS (Uninterruptible Power Supply):** Backup battery system to maintain power during outages

**YOLO (You Only Look Once):** Real-time object detection algorithm often used in traffic monitoring

### Traffic Monitoring Terms

**Direction:** Direction of vehicle travel (typically inbound/outbound, northbound/southbound, etc.)

**Speed Violation:** Vehicle traveling faster than the configured speed limit

**Traffic Analytics:** Statistical analysis of traffic patterns, volumes, and trends

**Traffic Volume:** Number of vehicles detected within a specific time period

**Vehicle Classification:** Categorization of vehicles by type (passenger car, truck, motorcycle, bus)

### Abbreviations

- **AI:** Artificial Intelligence
- **API:** Application Programming Interface
- **CSI:** Camera Serial Interface
- **CSV:** Comma-Separated Values
- **DHCP:** Dynamic Host Configuration Protocol
- **EMI:** Electromagnetic Interference
- **GPIO:** General Purpose Input/Output
- **HTTP:** Hypertext Transfer Protocol
- **HTTPS:** HTTP Secure
- **IP:** Internet Protocol (also: Ingress Protection for weatherproofing)
- **JSON:** JavaScript Object Notation
- **LED:** Light-Emitting Diode
- **ML:** Machine Learning
- **NPU:** Neural Processing Unit
- **OS:** Operating System
- **PDF:** Portable Document Format
- **PWA:** Progressive Web App
- **REST:** Representational State Transfer
- **ROI:** Region of Interest
- **SSD:** Solid-State Drive
- **SSH:** Secure Shell
- **SSL/TLS:** Secure Sockets Layer / Transport Layer Security
- **UART:** Universal Asynchronous Receiver-Transmitter
- **UI:** User Interface
- **UPS:** Uninterruptible Power Supply
- **URL:** Uniform Resource Locator
- **USB:** Universal Serial Bus
- **VPN:** Virtual Private Network
- **WiFi:** Wireless Fidelity

---

## Appendices

### A. Future Enhancements

**Current Mobile Access:** The dashboard is responsive and works on mobile browsers. You can add it to your home screen for quick access.

**Potential future enhancements may include:**
- **Native Mobile Apps:** Dedicated iOS and Android apps with push notifications
- **User Customization:** Advanced user roles, permissions, and dashboard customization
- **Accessibility Improvements:** Enhanced UI accessibility with screen reader support
- **Automated Alerts:** Flexible, user-defined alerting and notification options
- **Multi-Site Management:** Support for managing multiple installations from a single dashboard
- **Advanced Analytics:** Machine learning for traffic prediction and anomaly detection
- **License Plate Recognition:** Optional LPR integration for enforcement applications (subject to privacy regulations)
- **Data Export Options:** Enhanced data export capabilities for analysis and reporting

### B. Related Documentation

For additional information, please refer to:

- **Technical Design Document:** Detailed system architecture, hardware specifications, and software design
- **Implementation & Deployment Guide:** Step-by-step installation and configuration instructions
- **Project Management Summary:** Project planning, timeline, and deliverables
- **References & Appendices:** Additional resources, references, and supplementary information

### C. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | December 11, 2025 | Documentation Team | Initial release |
| 1.1 | December 15, 2025 | Documentation Team | Added troubleshooting sections |
| 1.2 | December 20, 2025 | Documentation Team | Restructured with standard user guide format |

### D. Acknowledgments

This project was developed as part of the CST 590 Computer Science Capstone Project. Special thanks to:

- Grand Canyon University Computer Science Department
- Raspberry Pi Foundation for hardware platform
- Sony Corporation for IMX500 AI camera technology
- OmniPreSense for OPS243-C radar sensor
- Open source community for Docker, Python, and related tools

---

**End of User Guide**

For questions or feedback about this documentation, please contact the project team or open an issue on GitHub.
