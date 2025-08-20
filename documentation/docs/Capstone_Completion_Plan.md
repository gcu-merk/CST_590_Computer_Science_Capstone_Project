
# Capstone Completion Plan

## Phased Implementation Overview
> **Note:**
> This plan is guided by a Minimal Viable Product (MVP)-first approach, emphasizing incremental development, future extensibility, and robust risk management. The project is structured so that Phase 1 delivers a working MVP, with subsequent phases designed for future implementation as time and resources allow. For full feedback and rationale, see [AI Feedback for Capstone Completion plan](../archive/AI%20Feedback%20for%20Capstone%20Completion%20plan.txt).

## Phased Implementation Overview

> **Note:**
> This plan is guided by a Minimal Viable Product (MVP)-first approach, emphasizing incremental development, future extensibility, and robust risk management. The project is structured so that Phase 1 delivers a working MVP, with subsequent phases designed for future implementation as time and resources allow. For full feedback and rationale, see [AI Feedback for Capstone Completion plan](../archive/AI%20Feedback%20for%20Capstone%20Completion%20plan.txt).

> **Note:**
> This plan is guided by a Minimal Viable Product (MVP)-first approach, emphasizing incremental development, future extensibility, and robust risk management. The project is structured so that Phase 1 delivers a working MVP, with subsequent phases designed for future implementation as time and resources allow. For full feedback and rationale, see [AI Feedback for Capstone Completion plan](../archive/AI%20Feedback%20for%20Capstone%20Completion%20plan.txt).

The project is delivered in four major phases, each building on the previous:

### Phase 1: Core Detection

- Integrate Sony IMX500 camera and basic hardware
- Deploy YOLOv8 object detection (pre-trained)
- Implement basic object tracking (SORT/DeepSORT)
- Simple speed calculation using radar FFT

### Phase 2: Advanced Processing

- Custom motion analysis and vehicle velocity calculation
- Lane detection and basic sensor fusion
- Traffic analytics and pattern recognition

### Phase 3: Intelligent Systems

- Advanced sensor fusion (ML-based)
- Anomaly detection and predictive analytics
- Adaptive learning and system self-improvement

### Phase 4: Optimization

- Performance optimization for real-time processing
- Environmental adaptation (weather, lighting)
- Advanced calibration and meta-learning

Each milestone/component in the plan below is mapped to its corresponding phase for clarity and traceability.

## Capstone Milestones Overview

| Milestone | Description | Key Components/Deliverables |
|-----------|-------------|----------------------------|
| 1 | Project Proposal & Requirements Analysis | Proposal document, requirements, work breakdown structure (WBS), schedule, risk management, scope, objectives, assumptions, constraints, roles, cost estimate, issues log |
| 2 | Architectural Design / Model Pipeline Design | System architecture, design planning summary, high-level and detailed design diagrams (UML, ERD, workflows), model pipeline (if DSC), technical specs, security plan, packages/libraries list |
| 3 | Implementation | Source code, mapping requirements to modules/functions, implementation plan (deployment, integration), code documentation, requirements review and updates |
| 4 | Performance Analysis & Presentation | Testing process document (test cases, results), requirements testing, system testing, operation & maintenance docs (user/admin guide), final code, screencast/video presentation, evaluation, milestone review, final submission |

---

This document lists all required capstone components grouped by milestone. For each component, the following are tracked:

- **Current Status**
- **Requirements for Desired Performance (if revision needed)**
- **Completion Date**
- **Resources Needed**
- **Reference Link**

---

## Milestone 1: Project Proposal & Requirements Analysis

| Phase | Component | Current Status | Requirements for Desired Performance | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 1 | Project name, author, org, manager, date | In Progress | Accurate, up-to-date info | Week 1 |  | [Technical Design: Top](./Technical_Design.md) |
| Phase 1 | Project overview (problem, background, objectives, challenges, benefits) | In Progress | Clear, concise, addresses all prompts. Objectives: (1) Evaluate effectiveness of a Raspberry Pi-based speed detection system for accuracy, reliability, cost-effectiveness, and community impact. (2) Provide an accessible, low-cost alternative to traditional systems. | Week 1 |  | [Technical Design: System Overview](./Technical_Design.md#1-system-overview) |
| Phase 1 | Project scope & work breakdown | In Progress | Complete WBS, all tasks identified | Week 1 |  | [Project Management: Implementation Timeline](./Project_Management.md#1-implementation-timeline) |
| Phase 1 | Project completion criteria | Not Started | 1. Accuracy: System detects vehicle speeds within ±5% of manual tools. 2. Cost-Effectiveness: At least 50% lower cost than traditional systems. 3. Reliability: Consistent operation under varied conditions. 4. Data Quality: Accurate, analyzable data logged. 5. Community Impact: Positive feedback and measurable safety improvements. | Week 2 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 1 | Assumptions and constraints | In Progress | Assumptions: Affordable/reliable components available; seamless integration; technical expertise available; community support; internet access. Constraints: Budget, timeline, resources, environmental conditions, regulatory compliance. | Week 2 |  | [Technical Design: System Overview](./Technical_Design.md#1-system-overview) |
| Phase 1 | Risk management plan | In Progress | Risks: Sensor accuracy, hardware incompatibility, algorithm performance, data loss, unauthorized access, privacy, budget, legal/IP compliance. Mitigation: Testing, backups, encryption, clear communication, budget monitoring, legal review. | Week 2 |  | [Project Management: Risk Management Matrix](./Project_Management.md#3-risk-management-matrix--contingency-planning) |
| Phase 1 | Change control log | Not Started | Track all changes/decisions | Week 2 |  | [Documentation TODO: Outstanding Tasks](./Documentation_TODO.md#1-outstanding-tasks) |
| Phase 1 | Roles and responsibilities | In Progress | All team roles defined | Week 2 |  | [Project Management: Executive Summary](./Project_Management.md#executive-summary) |
| Phase 1 | Project schedule & milestones | In Progress | Realistic, buffer time included | Week 2 |  | [Project Management: Implementation Timeline](./Project_Management.md#1-implementation-timeline) |
| Phase 1 | Cost estimate | Not Started | All costs accounted for | Week 2 |  | [Project Management: Budget & Cost Estimates](./Project_Management.md#2-budget--cost-estimates) |
| Phase 1 | Issues log | Not Started | Ongoing issue tracking | Week 2 |  | [Documentation TODO: Outstanding Tasks](./Documentation_TODO.md#1-outstanding-tasks) |

## Milestone 2: Architectural Design

| Phase | Component | Current Status | Requirements for Desired Performance | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 2 | Design planning summary | Not Started | Overview, rationale, issues addressed. Includes system context, design goals, and fit within overall project. | Week 3 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 2 | High-level design (narrative, mockups, flowcharts) | In Progress | All major flows and UI mocked | Week 3 |  | [Technical Design: System Architecture](./Technical_Design.md#2-system-architecture) |
| Phase 2 | Detailed solution architecture (UML, ERD, workflows) | In Progress | All diagrams complete and accurate. Includes object/data definitions, UML, ERD, workflow diagrams, database schema, and detailed flowcharts. | Week 4 |  | [Technical Design: Table of Contents](./Technical_Design.md#table-of-contents) |
| Phase 2 | Collaboration/sequence diagrams | Not Started | All key interactions diagrammed. Includes collaboration and/or sequence diagrams to show workflows of components/packages/classes. | Week 4 |  | [Technical Design: Sequence Diagram](./Technical_Design.md#5-sequence-diagram-typical-event-flow) |
| Phase 2 | Algorithm descriptions & performance analysis | In Progress | All core algorithms described, with detailed performance analysis and metrics. | Week 4 |  | [Technical Design: Top-Down Approach](./Technical_Design.md#2x-top-down-approach) |
| Phase 2 | Detailed specs for screens, interfaces, integration | In Progress | All specs documented. Includes all screens, interfaces, integration points, processes, conversion, and reports. | Week 4 |  | [Technical Design: Detailed Specs](./Technical_Design.md#detailed-specs-for-screens-interfaces-integration) |
| Phase 2 | Packages, libraries, hardware/software listed | In Progress | All dependencies listed. Includes all packages, software libraries, hardware, and software technologies used. | Week 4 | Raspberry Pi 5, Sony IMX500, OPS243-C Radar, SSD, PoE, TensorFlow, OpenCV, Flask, Python, Raspbian OS, microSD card, power supply, enclosure | [Technical Design: Packages, Libraries, Hardware/Software](./Technical_Design.md#packages-libraries-hardwaresoftware) |
| Phase 2 | Security approach and resources | In Progress | Security plan documented. Describes approach and resources required to assure system security. | Week 4 | Encryption libraries, secure storage, firewall, VPN, HTTPS, audit logs | [Technical Design: Security/Data Flow Diagram](./Technical_Design.md#9-securitydata-flow-diagram) |

## Milestone 3: Implementation

| Phase | Component | Current Status | Requirements for Desired Performance | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 3 | Mapping of requirements to modules/functions | Not Started | All requirements mapped. Functional requirements mapped to modules/functions, with diagrams and descriptions. | Week 5 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 3 | Source code listing & class/file descriptions | In Progress | All code documented. Well-organized, commented code with descriptions of classes/files. | Week 6 |  | [Technical Design: Component Interaction Diagram](./Technical_Design.md#4-component-interaction-diagram) |
| Phase 3 | Implementation plan (deployment, integration) | In Progress | All steps clear and testable. Comprehensive description of software, deployment, integration, and operational strategy. | Week 6 |  | [Implementation_Deployment.md](./Implementation_Deployment.md) |
| Phase 3 | Requirements review and updates | Not Started | All changes tracked. Includes code review summary and feedback. | Week 6 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |

## Milestone 4: Performance Analysis & Presentation

| Phase | Component | Current Status | Requirements for Desired Performance | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 4 | Testing process document (test cases, results) | In Progress | All modules tested, results logged | Week 7 |  | [Project Management: Quality Assurance & Testing Protocols](./Project_Management.md#4-quality-assurance--testing-protocols) |
| Phase 4 | Requirements testing (mapping to test scenarios) | Not Started | All requirements tested | Week 7 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 4 | System testing (end-to-end, data flows) | In Progress | All flows tested | Week 7 |  | [Project Management: Quality Assurance & Testing Protocols](./Project_Management.md#4-quality-assurance--testing-protocols) |
| Phase 4 | Operation & maintenance docs (user/admin guide) | In Progress | All guides complete | Week 7 |  | [User Guide](./User_Guide.md) |
| Phase 4 | Project completion (final code, docs, video) | Not Started | All deliverables ready | Week 8 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 4 | Evaluation (milestone review, improvements) | Not Started | All gaps identified | Week 8 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 4 | Final project submission (code, docs, README, video) | Not Started | All files submitted | Week 8 |  | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |

## Academic Integrity & References

| Component | Current Status | Requirements for Desired Performance | Completion Date | Resources Needed |
|-----------|---------------|--------------------------------------|-----------------|------------------|
| Academic integrity & plagiarism policy | Ongoing | All work original or cited | Ongoing |  |
| References and sources cited | Ongoing | All sources properly cited | Ongoing |  |
