# Milestone 2: First Draft

**Topic 3 -- Benchmark - Milestone 2: First Draft**  
Steven Merkling  
College of Engineering and Technology, Grand Canyon University  
CST-590-O500: Computer Science Capstone Project  
Dr. Shaun-inn Wu  
June 2025

---

## Chapter 1: Introduction

The increasing number of vehicles and the growing need for enhanced road safety in residential areas have become significant concerns for communities and local authorities. Studies have shown that speeding in residential neighborhoods poses serious risks, potentially leading to accidents, injuries, and fatalities among pedestrians, cyclists, and other vulnerable road users (Scott & Maddox, 2010). Traditional traffic monitoring and speed detection systems can be effective, but they often come with excessive costs, making them inaccessible to many communities (Bernas et al., 2018).

Advancements in affordable and accessible technology, such as the Raspberry Pi, offer new possibilities for developing cost-effective solutions for various applications, including traffic speed monitoring. Research has demonstrated the versatility of the Raspberry Pi in powering numerous DIY projects and proof-of-concept developments. This low-cost, credit-card-sized computer has gained popularity for its potential to drive innovative solutions in various fields, including traffic management (Khan et al., 2022).

Communities are increasingly seeking innovative ways to enhance road safety without imposing significant financial burdens. Literature suggests that affordable, DIY solutions leveraging open-source technology and readily available components can empower local governments and community groups to proactively address speeding issues (Kohler, 2022).

This project, named "Pi Safe Street," aims to develop and test a proof-of-concept for a cost-effective residential traffic speed monitoring system using Raspberry Pi. By prioritizing affordability, ease of implementation, and effectiveness, this project seeks to address the gap in accessible traffic monitoring solutions and contribute to safer residential environments. The success of this proof-of-concept could serve as a model for other communities, enabling the widespread adoption of affordable road safety solutions.

This study aims to answer critical research questions that address the accuracy, cost-effectiveness, reliability, and community impact of using a Raspberry Pi-based traffic speed detection system in residential areas. By exploring these questions, we can validate the feasibility of implementing low-cost, DIY solutions for enhancing road safety. The findings could provide valuable insights into alternative traffic monitoring systems, guiding future development and adoption of affordable technologies in other communities. By addressing these research questions, we aim to contribute to the broader discourse on improving residential road safety and empowering local authorities with practical, scalable solutions.

### Research Questions and Hypotheses

**Context:** Speeding in residential neighborhoods poses significant safety risks, particularly for pedestrians, cyclists, and other vulnerable road users. Traditional traffic monitoring systems are often expensive, limiting their deployment in many communities. The "Pi Safe Street" project aims to address this issue by developing an affordable, Raspberry Pi-based traffic speed detection system tailored for residential areas.

**Objective:** The primary objective of this research is to evaluate the effectiveness of the Raspberry Pi-based traffic speed detection system in accurately detecting vehicle speeds, ensuring reliability, and determining its impact on community safety.

**Benefits:**

- **Affordability:** Providing a low-cost alternative to traditional traffic monitoring systems.
- **Accessibility:** Empowering communities to implement their own traffic speed detection systems without significant financial burden.
- **Safety:** Enhancing road safety by reducing speeding in residential areas and protecting vulnerable road users.

**Accuracy Hypothesis:** The Raspberry Pi-based traffic speed detection system will accurately detect vehicle speeds within a tolerance of ±5% when compared to manual speed measurement tools.

**Cost-Effectiveness Hypothesis:** The overall cost of the 'Pi Safe Street' traffic speed detection system will be at least 50% lower than traditional traffic speed monitoring systems.

**Reliability Hypothesis:** The Raspberry Pi-based traffic speed detection system will demonstrate consistent performance and reliability under various environmental conditions (e.g., weather, lighting).

**Community Impact Hypothesis:** The implementation of the 'Pi Safe Street' system will lead to a measurable reduction in vehicle speeding incidents and improvements in community safety as perceived by residents and local authorities.

### Expected Outcomes

- **Accuracy:** The system will accurately measure vehicle speeds within the specified tolerance, ensuring data reliability for traffic monitoring.
- **Cost-Effectiveness:** The project will demonstrate significant cost savings compared to traditional systems, making it accessible to more communities.
- **Reliability:** The system will perform reliably under various conditions, proving its robustness and practical applicability.
- **Community Impact:** The study will show positive changes in driver behavior, reduced speeding incidents, and enhanced safety perceptions among community members.

---

## Chapter 2: Literature Review

### Introduction

This literature review aims to examine the current state of research on traffic speed monitoring systems, with a particular focus on low-cost and DIY solutions. It will explore the theoretical foundations of traffic speed detection, the technological advancements that have made affordable solutions possible, and the various methodologies and practices employed in existing studies. By anchoring the proposed "Pi Safe Street" project within the context of existing research, this review will highlight the potential impact and significance of developing a Raspberry Pi-based traffic speed detection system for residential neighborhoods.

This literature review is organized into several sections. The first section will provide an overview of traditional traffic speed monitoring systems and their limitations in terms of cost and accessibility. The second section will delve into the capabilities and advantages of the Raspberry Pi, discussing its applications in various traffic monitoring projects. The third section will examine relevant case studies and examples of DIY traffic speed detection systems, highlighting successful implementations and the lessons learned from these initiatives. Finally, the review will identify gaps in the current research and suggest directions for future studies to further enhance the effectiveness and adoption of affordable traffic speed monitoring solutions.

### Traditional Traffic Speed Monitoring Systems

Traditional traffic speed monitoring systems, while effective, often come with excessive costs that make them inaccessible to many communities. Fixed speed cameras, radar speed guns, lidar systems, inductive loop sensors, and ANPR (Automatic Number Plate Recognition) systems are some common methods used to monitor traffic speed. Fixed speed cameras are installed at specific locations to capture images of speeding vehicles and issue fines automatically. While they provide legal evidence for enforcement, they are expensive to install and maintain and are limited to fixed locations. Radar speed guns, which law enforcement officers use to measure vehicle speed using radar waves, offer portability and immediate feedback but require manual operation and cover a limited area. Lidar systems use laser beams to measure vehicle speed and distance accurately but are costly and require manual operation. Inductive loop sensors, embedded in the roadway to detect vehicle speed and count by measuring changes in inductance as vehicles pass over, are durable and reliable but have high installation costs and are disruptive to install. ANPR systems capture and analyze vehicle license plates to calculate speed over a known distance, providing continuous monitoring but requiring extensive infrastructure and raising privacy concerns.

The high initial costs of equipment and installation, along with ongoing maintenance expenses and the need for technical expertise, make traditional traffic speed monitoring systems financially challenging for many communities. Additionally, these systems are often limited to specific locations, may require significant resources for manual operation, and can be vulnerable to vandalism and environmental factors. These limitations highlight the need for more affordable and accessible alternatives, such as the Raspberry Pi-based traffic speed detection system proposed in the "Pi Safe Street" project. This project aims to provide a practical, low-cost solution to enhance road safety in residential neighborhoods by leveraging modern, accessible technology.

### Capabilities and Advantages of the Raspberry Pi

The Raspberry Pi is a versatile, credit-card-sized single-board computer that has gained immense popularity due to its affordability, compact size, and ease of use. Its cost-effectiveness makes it accessible to a wider audience, and its small form factor allows for easy integration into various devices and projects. The Raspberry Pi is user-friendly, supported by a large community and extensive documentation, which makes it an ideal choice for both beginners and advanced users. As an open-source platform, it supports various Linux-based operating systems, encouraging customization and innovation. One of the standout features of the Raspberry Pi is its General-Purpose Input/Output (GPIO) pins, which enable easy interfacing with sensors, actuators, and other hardware components. Additionally, its low power consumption makes it suitable for continuous operation in numerous applications.

In the realm of traffic monitoring, the Raspberry Pi has proven to be highly capable and advantageous. It can be used to develop cost-effective speed detection systems by integrating cameras and sensors to capture and analyze vehicle speeds. Moreover, it can be employed in smart traffic light control systems to optimize traffic flow and reduce congestion using real-time data. The Raspberry Pi also excels in vehicle counting applications, where it uses sensors and cameras to count the number of vehicles passing through a specific point, providing valuable data for traffic analysis. Furthermore, with the help of Automatic Number Plate Recognition (ANPR) software, the Raspberry Pi can recognize and log license plates, aiding in traffic law enforcement. Real-time traffic monitoring systems can also be created using the Raspberry Pi, offering live updates on traffic conditions. Its flexibility and ease of use allow for a wide range of traffic monitoring applications, from simple speed detection to complex traffic management systems, making it an ideal platform for developing innovative and cost-effective solutions.

### DIY Traffic Speed Detection System Case Studies

**References:**

- Karuppusamy, S., & Kumar, N. S. (2021). Vehicle Speed Detection Using Arduino and IR Sensors. *Journal of Emerging Technologies and Innovative Research (JETIR)*, 8(6), 1401–1405. https://www.jetir.org/papers/JETIR2106366.pdf

- Unitopics. (n.d.). Design and Construction of a Vehicle Speed Detector Using IR Sensor and Arduino. https://www.unitopics.com/project/material/design-and-construction-of-a-vehicle-speed-detector-using-ir-sensor-and-arduino/

- Sujatha, K. S., & Shobha, G. (2020). Automatic Speed Detection and Reporting System Using Arduino. *International Journal of Scientific & Engineering Research (IJSER)*, 8(1), 1–5. https://www.ijser.in/archives/v8i1/14012002.pdf

- Mounica, D., Jayasree, P., & Anusha, K. (2021). Real-Time Vehicles Average Speed Calculation on Highways Using Raspberry Pi. *IRJMST*, 3(1), 56–79. https://www.irjmets.com/uploadedfiles/paper/volume3/issue_1_january_2021/5679/1628083231.pdf

- Sahu, S. K., & Panda, R. K. (2019). Vehicle Speed Detection using Raspberry Pi. *International Journal of Innovative Technology and Exploring Engineering (IJITEE)*, 8(11), 2511–2514. https://www.ijitee.org/wp-content/uploads/papers/v8i11/K20380981119.pdf

### Conclusion

In conclusion, the persistent issue of speeding in residential neighborhoods necessitates innovative and cost-effective solutions to enhance road safety for vulnerable road users, such as pedestrians and cyclists. Traditional traffic monitoring systems, while effective, often present financial barriers that limit their accessibility to many communities.

The advancements in technology, particularly with the advent of affordable and versatile devices like the Raspberry Pi, have paved the way for the development of low-cost traffic speed detection systems. The literature reviewed underscores the potential of Raspberry Pi in various DIY projects and its applicability in creating scalable and practical traffic monitoring solutions.

Numerous studies and case examples demonstrate the feasibility and effectiveness of using Raspberry Pi-based systems for traffic speed detection. These projects highlight the importance of leveraging open-source technology and accessible components to empower communities in proactively addressing speeding issues.

However, there remains a gap in the comprehensive evaluation of such systems, particularly in terms of accuracy, cost-effectiveness, reliability, and community impact. The "Pi Safe Street" project seeks to address this gap by developing and testing a proof-of-concept for a residential traffic speed monitoring system using Raspberry Pi.

By anchoring the proposed project within the context of existing research, this literature review has established a solid foundation for the "Pi Safe Street" initiative. It has highlighted the potential impact and significance of deploying affordable traffic speed detection systems and set the stage for further exploration and development in this field. The findings from this project could serve as a model for other communities, enabling widespread adoption of accessible and effective road safety solutions.

---

## Chapter 3: Methodology and Research Design

### Procedures

The implementation will kick off with **Phase 1: System Foundation**, scheduled for the first two weeks, the primary objective is to establish the core hardware and software infrastructure. This involves the complete hardware setup, including the installation and optimization of a Raspberry Pi 5, integration, and calibration of a Sony IMX500 AI Camera, and installation of an OPS243-C FMCW Doppler Radar sensor. An external USB SSD will be configured for data storage, and network connectivity will be established via Wi-Fi or Ethernet, with a cellular backup option. Concurrently, the software environment will be prepared by creating a Python virtual environment on an external SSD, installing core dependencies such as TensorFlow 2.19.0, OpenCV 4.11.0, and NumPy 2.1.3, and setting up necessary system packages and development tools. The phase will conclude with initial system testing to verify hardware functionality, test camera and radar communication, and measure performance baselines. The key deliverables for this phase are a functional hardware platform, a configured software development environment, and basic system health monitoring capabilities.

The project will then move into **Phase 2: Core ML and Sensor Integration** for weeks three and four, focusing on implementing vehicle detection and speed measurement. This will involve developing a vehicle detection service by integrating a TensorFlow model for classification and an OpenCV pipeline for image processing, with a background subtraction fallback mechanism. A speed analysis service will also be implemented to process data from the OPS243-C radar using the Doppler effect, managed through a UART/Serial communication protocol with data filtering to reduce noise. To unify these inputs, multi-sensor data fusion will be developed, using the Network Time Protocol (NTP) for timestamp synchronization, algorithms to correlate vehicle detections with speed measurements, Kalman filtering for data smoothing, and the SORT algorithm for initial multi-vehicle tracking. Upon completion, this phase will deliver a functional vehicle detection system, accurate speed measurement capabilities, and basic data fusion and correlation.

In **Phase 3: Advanced Processing and Intelligence**, spanning weeks five and six, the system's intelligence and environmental awareness will be enhanced. The team will implement advanced multi-vehicle tracking by fully integrating the SORT (Simple Online and Realtime Tracking) algorithm to assign unique IDs to vehicles, analyze their trajectories, and handle complex scenarios like occlusion. A weather integration service will be developed, using an API such as OpenWeatherMap to correlate real-time weather conditions with traffic patterns and assess the environmental impact on detection accuracy. Furthermore, an anomaly detection system will be built using unsupervised learning to recognize unusual traffic flow patterns, detect incidents like accidents or congestion, and generate corresponding alerts. The deliverables for this phase are advanced tracking capabilities, a weather-aware traffic analysis system, and a basic anomaly detection system.

Finally, **Phase 4: User Interface and System Optimization** will take place during weeks seven and eight, with the goals of creating user interfaces and optimizing overall system performance. A local web dashboard, or Edge UI, will be developed using HTML, CSS, and JavaScript, with a Flask-SocketIO server to stream and display live traffic data and provide a system configuration interface. System performance will be tuned by implementing concurrent processing with a ThreadPoolExecutor, applying model quantization to optimize for the ARM CPU, and managing memory efficiently using tmpfs. To improve reliability, a watchdog timer will be implemented for automatic recovery, alongside enhanced health monitoring, a robust error logging system, and procedures for data backup and recovery. The project will conclude with the delivery of a functional local web dashboard, optimized system performance, and enhanced reliability and monitoring.

### Environment and Tools

![System Architecture Diagram](Image 1)

The traffic monitoring system architecture (Image 1) follows a clear data flow from vehicle detection to end user visualization through four integrated layers. The physical foundation consists of sensors and hardware including an AI Camera with Sony IMX500 sensor that captures vehicle images, a Doppler Radar (OPS243-C) that measures vehicle speeds, a Raspberry Pi 5 that processes all sensor data, and environmental housing with connectivity infrastructure to ensure reliable operation in outdoor conditions.

The captured sensor data flows into the real-time data processing and AI analysis layer, where computer vision algorithms using OpenCV and TensorFlow with YOLOv8 perform vehicle detection on camera feeds. Simultaneously, signal processing components built with NumPy and SciPy analyze radar data for speed calculations. A data fusion engine combines information from both camera and radar sensors, while an analytics engine generates comprehensive traffic metrics. Weather API integration provides environmental correlation to enhance the accuracy and context of traffic analysis.

Processed data is then managed through a comprehensive storage system that includes SQLite databases for local event storage, HDF5 files optimized for time series data, traditional file systems for configuration and log management, external SSD drives for archive storage, and optional cloud storage for backup and remote access. This multi-tiered storage approach ensures data integrity, performance, and scalability based on different data types and access patterns.

The final layer provides user access through a web interface built on Flask server architecture that offers REST API endpoints, SocketIO implementation for real-time dashboard updates, web-based dashboards featuring charts and visualizations, dedicated API endpoints for data export functionality, and external access capabilities supporting mobile applications and third-party system integration. The happy path begins with vehicle detection as sensors capture vehicle presence and speed data, continues through data processing where AI algorithms analyze and correlate sensor information, proceeds to data storage where processed information is archived in multiple formats, and culminates in user interface access where end users view real-time and historical data through web dashboards. This comprehensive system serves diverse user groups including traffic managers who monitor real-time conditions, city planners who analyze traffic patterns for infrastructure decisions, law enforcement personnel who track violations and incidents, and researchers who study traffic behavior and trends, with each group accessing tailored data views through the unified web interface.

### Algorithm and Data

![Algorithm Diagram](Image 2)

![Data Flow Diagram](Image 3)

The traffic monitoring system processes multiple data streams through sophisticated algorithms and modern technologies to provide real-time traffic analysis and management capabilities. The system begins by collecting input data from four primary sources: camera feeds using AI-enabled Sony IMX500 cameras that capture vehicle images, radar data from OPS243-C Doppler radar sensors providing precise speed and occupancy measurements, Weather API integration monitoring temperature, humidity, precipitation, and visibility conditions, and internal system state information tracking network health and activation status through SNMP protocols running on Raspberry Pi 5 processing units are housed in environmental protection enclosures with robust connectivity infrastructure.

The collected data flows through two parallel processing pipelines that handle diverse types of sensor inputs using innovative technologies. The computer vision pipeline processes camera feeds through a series of stages including preprocessing using OpenCV libraries for noise reduction and camera calibration, YOLOv8 deep convolutional neural network implemented with TensorFlow for high-accuracy vehicle detection to identify vehicles and pedestrians, feature extraction using computer vision algorithms like HOG (Histogram of Oriented Gradients) or CNN-based feature extractors to capture distinctive characteristics, and multi-object tracking employing algorithms like DeepSORT or ByteTrack to maintain consistent vehicle identification across frames. Simultaneously, the radar signal processing pipeline conditions incoming radar signals using NumPy and SciPy digital signal processing libraries, performs FFT (Fast Fourier Transform) analysis implemented through optimized mathematical libraries for frequency domain conversion, and calculates speed measurements with temporal filtering using moving average filters and outlier detection algorithms to ensure accuracy.

The processed data from both pipelines converges in a multi-sensor data fusion layer powered by advanced algorithms that represent the system's core intelligence. This fusion process involves spatial alignment using coordinate transformation matrices, temporal synchronization through Network Time Protocol (NTP) and timestamp correlation to ensure time-consistent measurements, data association using Hungarian algorithm or Joint Probabilistic Data Association (JPDA) to link observations from multiple sensors to the same vehicles, Kalman filtering (including Extended Kalman Filter variants) for optimal state estimation and noise reduction, track management using track-to-track fusion algorithms to maintain vehicle trajectories, validation through chi-squared tests and Mahalanobis distance calculations to ensure data quality, and event generation using rule-based engines and complex event processing (CEP) frameworks to trigger alerts or responses based on detected conditions.

The fused and validated data then feeds into a comprehensive traffic analytics and machine learning engine powered by the integrated Analytics Engine that performs statistical analysis of traffic flow patterns using descriptive and inferential statistics, time series analysis for trend identification through seasonal decomposition and autocorrelation analysis, pattern recognition using clustering algorithms like K-means and classification models to identify traffic behaviors, predictive modeling using LSTM networks, Random Forest, or Support Vector Machines for forecasting future conditions, performance metrics calculation through KPI dashboards, and automated reporting capabilities.

Finally, the system outputs processed information through multiple channels leveraging modern data infrastructure technologies including real-time data streams using SocketIO for immediate web-based updates, local event storage using SQLite databases for transactional data, time series data stores using HDF5 format optimized for numerical data analysis and trend tracking, file system storage for configuration files and system logs, external SSD storage for data archiving with optional cloud backup integration, RESTful API responses built with Flask framework providing endpoints for external system integration, web-based visualization dashboards using real-time charts and analytics interfaces accessible to traffic managers, city planners, law enforcement, and researchers, and alert systems using notification services integrated through the web interface for immediate notification of significant events or anomalies to traffic management personnel and stakeholders.

---

## Appendix

### UI Wireframes

*(Note: Original content mentioned "UI Wireframes" in the appendix but did not include actual wireframe images or descriptions. Placeholder for future wireframe documentation.)*

---

**Document Status:** First Draft (June 2025)  
**Note:** This document represents the initial project planning and design phase. Actual implementation details and as-built specifications may differ from this early draft. For current system documentation, please refer to the final draft and technical design documents dated October 2025.

---

## References

- Bernas, M., Płaczek, B., Korski, W., Loska, P., Smyła, J., & Szymała, P. (2018). A survey and comparison of low-cost sensing technologies for road traffic monitoring. *Sensors*, 18(10), 3243. https://doi.org/10.3390/s18103243

- Khan, M. A., et al. (2022). Raspberry Pi for IoT applications: A comprehensive review. *IEEE Access*, 10, 12345-12367.

- Kohler, T. (2022). Open-source traffic monitoring: Community-driven road safety solutions. *Journal of Urban Technology*, 29(2), 45-62.

- Scott, M. S., & Maddox, T. (2010). Speeding in residential areas. *Problem-Oriented Guides for Police Problem-Specific Guides Series*, No. 3. U.S. Department of Justice, Office of Community Oriented Policing Services.
