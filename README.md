# CST_590_Computer_Science_Capstone_Project
Raspberry Pi-based system detects speeding and stop sign violations, improving road safety. Uses computer vision and AI for real-time monitoring and data analysis.
## Raspberry Pi-Based Traffic Violation Detection System

**Overview**

This project aims to develop a Raspberry Pi-based system capable of detecting speeding vehicles and stop sign violations in residential areas. By leveraging computer vision techniques and machine learning algorithms, the system can contribute to improved road safety and traffic management.

**Key Features:**

* Real-time detection of speeding vehicles and stop sign violations
* Accurate vehicle speed estimation
* Data collection and analysis for traffic insights
* Customizable alert system for notifications

**Technical Implementation:**

* **Hardware:** Raspberry Pi, camera module, power supply
* **Software:** Python, OpenCV, TensorFlow/Keras
* **Computer Vision:** Object detection, tracking, and speed estimation
* **Machine Learning:** Model training for accurate detection and classification

**Installation:**

1. **Hardware Setup:**
   - Assemble the Raspberry Pi with the camera module.
   - Ensure proper power supply and SD card setup.
2. **Software Installation:**
   - Install the required Python libraries (OpenCV, TensorFlow/Keras, etc.).
   - Clone the project repository.
3. **Configuration:**
   - Adjust camera settings and calibration parameters.
   - Configure the detection and alert thresholds.
4. **Deployment:**
   - Deploy the system to a suitable location with clear camera view.
   - Run the script to start the detection process.

**Usage:**

1. **Data Collection:** The system will continuously capture video frames and process them.
2. **Vehicle Detection:** Objects are detected and classified as vehicles.
3. **Speed Estimation:** Vehicle speed is calculated based on frame-to-frame motion analysis.
4. **Violation Detection:** Speeding and stop sign violations are identified.
5. **Alert Generation:** Alerts are triggered and sent to specified recipients.

**Future Work:**

* Improve detection accuracy in challenging lighting conditions.
* Explore advanced deep learning techniques for better performance.
* Integrate with cloud-based platforms for remote monitoring and analysis.
* Develop a user-friendly interface for system configuration and data visualization.

**Contributing:**

We welcome contributions to this project after August 2025. Please feel free to fork the repository and submit pull requests.

Repo Structure

RaspberryPi-Traffic-Violation-Detection/
│
├── data-collection/
│   ├── README.md
│   ├── speed-data-collection/
│   │   ├── speed_data_collection.py
│   │   └── requirements.txt
│   ├── stop-sign-data-collection/
│   │   ├── stop_sign_data_collection.py
│   │   └── requirements.txt
│   ├── license-plate-data-collection/
│   │   ├── license_plate_data_collection.py
│   │   └── requirements.txt
│   ├── data-consolidator/
│   │   ├── data_consolidator.py
│   │   └── requirements.txt
│   ├── data-persister/
│   │   ├── data_persister.py
│   │   └── requirements.txt
│   └── utils/
│       ├── utils.py
│       └── requirements.txt
│
├── webserver/
│   ├── README.md
│   ├── src/
│   │   ├── main.ts
│   │   ├── app.module.ts
│   │   ├── controllers/
│   │   │   ├── data.controller.ts
│   │   │   └── camera.controller.ts
│   │   ├── services/
│   │   │   ├── data.service.ts
│   │   │   └── camera.service.ts
│   │   ├── database/
│   │   │   ├── database.module.ts
│   │   │   └── database.service.ts
│   └── package.json
│
├── database/
│   ├── README.md
│   ├── init_db.sql
│   ├── schema/
│   │   ├── create_tables.sql
│   ├── scripts/
│   │   ├── data_import.sh
│   └── backups/
│       ├── backup_20241203.sql
│
├── website/
│   ├── README.md
│   ├── public/
│   │   ├── index.html
│   └── src/
│       ├── App.js
│       ├── components/
│       │   ├── CameraView.js
│       │   ├── LogsView.js
│       └── package.json
│
├── mobile/
│   ├── README.md
│   ├── android/
│   ├── ios/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── views/
│   │   │   ├── camera_view.dart
│   │   │   └── logs_view.dart
│   └── pubspec.yaml
│
└── README.md
