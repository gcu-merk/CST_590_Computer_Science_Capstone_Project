# Use Cases for Raspberry Pi 5 Edge ML Traffic Monitoring System

This document organizes use cases by implementation priority: MVP (Minimum Viable Product), Early Iterations, and Later Iterations.

---

## MVP (Implement First)

> **Note:** For technical details on the AI camera, ML/AI workflow, and component status, see the [ML/AI Workflow and Component Status](./Technical_Design.md#31-mlai-workflow-and-component-status) section in the Technical Design Document.

### 1. System Detects and Logs Speeding Vehicle

**Sequence of Actions:**

1. Vehicle passes through sensor area.
2. AI Camera and Radar detect vehicle and speed.
3. Data Fusion Engine correlates camera and radar data.
4. Speeding event is logged and alert generated.
5. (Optional) Event sent to cloud for analytics.

**ASCII Diagram:**

```text
Vehicle
   |
   v
+--------+    +--------+    +--------+    +--------+    +--------+
| Camera |--->| Radar  |--->| Fusion |--->| Storage|--->| Cloud? |
+--------+    +--------+    +--------+    +--------+    +--------+
   2            2            3            4            5
```

---

### 2. Remote User Views Live Traffic Dashboard

**Sequence of Actions:**

1. User connects to Tailscale VPN.
2. User opens web browser and enters Pi’s Tailscale IP.
3. Edge UI authenticates user (if required).
4. Edge UI displays live traffic data and analytics.

**ASCII Diagram:**

```text
+--------+      +-------------+      +-------------------+
|  User  |----->| Tailscale   |----->| Raspberry Pi 5    |
|        |      |  Network    |      | (Edge UI/Web Dash)|
+--------+      +-------------+      +-------------------+
      1              2-3-4
```

---

### 3. Edge Device Handles Network Outage

**Sequence of Actions:**

1. Edge device loses connection to the cloud/network.
2. Local services continue to process and store data.
3. System queues events for later upload.
4. When network is restored, queued data is sent to the cloud.

**ASCII Diagram:**

```text
+-------------------+
| Raspberry Pi 5    |
| (Edge Device)     |
+-------------------+
        |
        v
+-------------------+
| Local Storage     |
+-------------------+
        |
        v
+-------------------+
|  Cloud Services   |
+-------------------+
   (when network restored)
```

---

### 4. User Receives Real-Time Speeding Alert

**Sequence of Actions:**

1. System detects a speeding vehicle.
2. Event triggers alert logic.
3. Alert is sent to user via dashboard or notification system.

**ASCII Diagram:**

```text
+--------+      +-------------------+      +-------------------+
| Radar  |----->| Raspberry Pi 5    |----->| User Dashboard    |
|/Camera |      | (Alert Logic)     |      |/Notification     |
+--------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 5. Admin Remotely Updates System Software

**Sequence of Actions:**

1. Admin connects via SSH over Tailscale.
2. Authenticates to Raspberry Pi.
3. Runs update commands (e.g., pulls new Docker images).
4. System restarts services with updated software.

**ASCII Diagram:**

```text
+--------+      +-------------+      +-------------------+
| Admin  |----->| Tailscale   |----->| Raspberry Pi 5    |
| (SSH)  |      |  Network    |      | (CLI/Services)    |
+--------+      +-------------+      +-------------------+
   1-2              1-2                3-4
```

---

### 6. Data Analyst Reviews Historical Traffic Data

**Sequence of Actions:**

1. Analyst logs into cloud dashboard.
2. Requests historical data and analytics.
3. Cloud services aggregate and present data.

**ASCII Diagram:**

```text
+----------+      +-------------------+      +-------------------+
| Analyst  |----->| Cloud Dashboard   |<-----| Cloud Database    |
+----------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 7. Device Self-Monitoring and Automated Recovery

**Sequence of Actions:**

1. System health monitor checks CPU, memory, and service status.
2. If an issue is detected (e.g., service crash), system attempts automated recovery (restart service or device).
3. Recovery action and status are logged and (optionally) reported to admin.

**ASCII Diagram:**

```text
+-------------------+
| Health Monitor    |
+-------------------+
        |
        v
+-------------------+
| Detect Issue?     |
+-------------------+
   | Yes      | No
   v         v
+--------+  +--------+
|Restart |  |  Log   |
|Service |  | Status |
+--------+  +--------+
```

---

### 8. Scheduled Data Backup to External SSD

**Sequence of Actions:**

1. System scheduler triggers backup routine.
2. Data is copied from local storage to external SSD.
3. Backup status is logged and (optionally) reported to admin.

**ASCII Diagram:**

```text
+-------------------+
| Raspberry Pi 5    |
| (Scheduler)       |
+-------------------+
        |
        v
+-------------------+
| Local Storage     |
+-------------------+
        |
        v
+-------------------+
| External SSD      |
+-------------------+
        |
        v
+-------------------+
| Log/Report        |
+-------------------+
```

---

## Early Iterations (After MVP)

### 9. Weather Data Integration for Contextual Analytics

**Sequence of Actions:**

1. Edge device queries weather API at scheduled intervals.
2. Weather data is stored locally and/or sent to cloud.
3. Traffic analytics incorporate weather context for improved accuracy.

**ASCII Diagram:**

```text
+-------------------+
| Raspberry Pi 5    |
| (Weather Query)   |
+-------------------+
        |
        v
+-------------------+
| Weather API       |
+-------------------+
        |
        v
+-------------------+
| Local/Cloud Store |
+-------------------+
        |
        v
+-------------------+
| Analytics Engine  |
+-------------------+
```

---

### 10. Edge Device Performs Anomaly Detection

**Sequence of Actions:**

1. Edge device processes incoming sensor data.
2. Anomaly detection algorithm identifies unusual traffic pattern or event.
3. System logs anomaly and (optionally) sends alert to admin or cloud.

**ASCII Diagram:**

```text
+-------------------+
| Sensors (Radar,   |
| Camera)           |
+-------------------+
        |
        v
+-------------------+
| Raspberry Pi 5    |
| (Anomaly Detect)  |
+-------------------+
        |
        v
+-------------------+
| Log/Alert/Cloud   |
+-------------------+
```

---

### 11. Automated System Health Reporting

**Sequence of Actions:**

1. Edge device periodically collects health and status data.
2. Device sends report to cloud or admin.
3. Admin reviews health reports for maintenance.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| Edge Device       |----->| Cloud/Admin       |----->| Maintenance Action|
+-------------------+      +-------------------+      +-------------------+
    1-2                2-3                        3
```

---

### 12. User Configures System Settings via Web UI

**Sequence of Actions:**

1. User accesses configuration panel in Edge UI.
2. User adjusts detection thresholds, alert settings, or network preferences.
3. System applies new settings and confirms changes.

**ASCII Diagram:**

```text
+--------+      +-------------------+      +-------------------+
|  User  |----->| Edge UI Config    |----->| System Settings   |
+--------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 13. Incident Video/Photo Retrieval

**Sequence of Actions:**

1. User or analyst requests video/photo for a specific event.
2. System locates and retrieves relevant media.
3. Media is presented to user/analyst for review.

**ASCII Diagram:**

```text
+--------+      +-------------------+      +-------------------+
|  User  |----->| Edge/Cloud Store  |----->| Media Viewer      |
+--------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 14. Edge Device Performs Local Data Retention Management

**Sequence of Actions:**

1. Device monitors storage usage and retention policy.
2. Old data is automatically deleted to free space.
3. System logs retention actions.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| Edge Device       |----->| Data Retention    |----->| System Log        |
+-------------------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 15. Remote Firmware Upgrade

**Sequence of Actions:**

1. Admin uploads new firmware/software image to cloud or management dashboard.
2. Edge device receives upgrade notification and downloads update.
3. Device verifies and applies the update.
4. System restarts and resumes normal operation.

**ASCII Diagram:**

```text
+--------+      +-------------------+      +-------------------+
| Admin  |----->| Cloud/Dashboard   |----->| Edge Device       |
+--------+      +-------------------+      +-------------------+
    1                  2                        3
                                            |
                                            v
                                   +-------------------+
                                   | Restart/Resume    |
                                   +-------------------+
                                        4
```

---

### 16. New Edge Device Onboarding

**Sequence of Actions:**

1. Technician installs new Raspberry Pi 5 and sensors at site.
2. Device is powered on and connects to Tailscale network.
3. Device registers with cloud or management dashboard.
4. System verifies configuration and begins normal operation.

**ASCII Diagram:**

```text
+-------------+      +-------------------+      +-------------------+
| Technician  |----->| New Edge Device   |----->| Tailscale Network |
+-------------+      +-------------------+      +-------------------+
    1                  2                        2
        |                                         |
        v                                         v
+-------------------+      +-------------------+
| Cloud/Dashboard   |<-----| Device Registers  |
+-------------------+      +-------------------+
    3                        3-4
```

---

## Later Iterations (Advanced/Enterprise/Compliance)

### 17. Privacy Request Handling (Data Deletion)

**Sequence of Actions:**

1. User submits a privacy/data deletion request via dashboard or cloud portal.
2. System locates relevant data (images, logs) associated with the request.
3. Data is securely deleted from local and/or cloud storage.
4. Confirmation is sent to the user.

**ASCII Diagram:**

```text
+--------+      +-------------------+      +-------------------+
|  User  |----->| Dashboard/Cloud   |----->| Edge/Cloud Store  |
+--------+      +-------------------+      +-------------------+
    1                  2                        3
                                            |
                                            v
                                   +-------------------+
                                   | Confirmation      |
                                   +-------------------+
                                        4
```

---

### 18. Multi-Site Data Aggregation and Comparison

**Sequence of Actions:**

1. Analyst accesses cloud dashboard.
2. Requests data from multiple edge devices/sites.
3. Cloud aggregates, compares, and visualizes data.

**ASCII Diagram:**

```text
+----------+      +-------------------+      +-------------------+
| Analyst  |----->| Cloud Dashboard   |<-----| Edge Device 1     |
+----------+      +-------------------+      +-------------------+
    1                  2                        2
                                            |
                                            v
                                   +-------------------+
                                   | Edge Device 2     |
                                   +-------------------+
                                        2
                                            |
                                            v
                                   +-------------------+
                                   | Aggregation/      |
                                   | Comparison        |
                                   +-------------------+
                                        3
```

---

### 19. Edge Device Supports Multiple Sensor Types

**Sequence of Actions:**

1. New sensor (e.g., sound, environmental) is connected to edge device.
2. Device auto-detects and integrates sensor data.
3. System uses new data for analytics and reporting.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| New Sensor        |----->| Edge Device       |----->| Analytics/Reports |
+-------------------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 20. Edge Device Integrates with Third-Party Services

**Sequence of Actions:**

1. Edge device detects event (e.g., speeding, anomaly).
2. Device sends event data to third-party API/service.
3. Third-party service processes and responds as needed.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| Edge Device       |----->| Third-Party API   |----->| External Service  |
+-------------------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 21. User Submits Feedback via Dashboard

**Sequence of Actions:**

1. User accesses Edge UI dashboard.
2. User fills out and submits feedback form.
3. Feedback is stored locally and/or sent to cloud for review.
4. Admin or analyst reviews feedback for system improvements.

**ASCII Diagram:**

```text
+--------+      +-------------------+      +-------------------+
|  User  |----->| Edge UI Dashboard |----->| Local/Cloud Store |
+--------+      +-------------------+      +-------------------+
    1                  2                        3
                                            |
                                            v
                                   +-------------------+
                                   | Admin/Analyst     |
                                   +-------------------+
                                        4
```

---

### 22. System Integrates with Cloud-Based Alerting/Notification Services

**Sequence of Actions:**

1. Event triggers alert logic on edge or cloud.
2. Alert is sent via cloud-based notification service (SMS, email, push).
3. User receives and acknowledges alert.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| Edge/Cloud Event  |----->| Notification Svc  |----->| User Device       |
+-------------------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

### 23. Edge Device Participates in Fleet Management

**Sequence of Actions:**

1. Multiple edge devices are registered with a central management system.
2. Central system pushes configuration, updates, and monitors all devices.
3. Admin reviews fleet status and issues commands as needed.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| Edge Devices      |<---->| Fleet Mgmt System |<---->| Admin             |
+-------------------+      +-------------------+      +-------------------+
    1                  2                        3
```

---

> **Note:** For more on model update workflow and inference, see the [ML/AI Workflow and Component Status](./Technical_Design.md#31-mlai-workflow-and-component-status) section in the Technical Design Document.

### 24. Edge Device Performs Local ML Model Update

**Sequence of Actions:**

1. Cloud service provides new ML model to edge device.
2. Device downloads and validates the model.
3. Device swaps in the new model for inference.
4. System logs update and resumes normal operation.

**ASCII Diagram:**

```text
+-------------------+      +-------------------+      +-------------------+
| Cloud Service     |----->| Edge Device       |----->| Inference Engine  |
+-------------------+      +-------------------+      +-------------------+
    1                  2-3                        4
```

---

Feel free to expand these use cases or add more as the system evolves.
