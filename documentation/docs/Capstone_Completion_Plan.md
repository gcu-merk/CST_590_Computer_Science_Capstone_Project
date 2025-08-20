
# Capstone Completion Plan

## Executive Summary

This project aims to deliver a robust, edge-based traffic monitoring system using a Raspberry Pi 5, AI camera, and radar sensor. The plan is structured in four phases, each mapped to clear milestones. As of now, Milestone 1 is 65% complete and on track for Week 2 delivery. Key risks include hardware integration and algorithm performance, both being actively mitigated. The following dashboard and sections provide a snapshot of progress, dependencies, and next steps.

## Phased Implementation Overview

> **Note:**
> This plan is guided by a Minimal Viable Product (MVP)-first approach, emphasizing incremental development, future extensibility, and robust risk management. The project is structured so that Phase 1 delivers a working MVP, with subsequent phases designed for future implementation as time and resources allow. For full feedback and rationale, see [AI Feedback for Capstone Completion plan](../archive/AI%20Feedback%20for%20Capstone%20Completion%20plan.txt) and [Peer Feedback for Capstone Completion plan](../archive/Capstone_Completion_Plan_Peer_Feedback.txt).

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

| Phase | Component | Current Status | Requirements for Desired Performance (with Feedback & Examples) | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 1 | Project name, author, org, manager, date | In Progress | Accurate, up-to-date info. Peer/instructor feedback: Confirmed correct format and naming conventions. Example: "Raspberry Pi 5 Edge ML Traffic Monitoring System". | Week 1 | Project charter template, instructor review | [Technical Design: Top](./Technical_Design.md) |
| Phase 1 | Project overview (problem, background, objectives, challenges, benefits) | In Progress | Clear, concise, addresses all prompts. Peer review: Objectives and challenges validated by team and instructor. Example: Objective to provide a low-cost, accurate speed detection system. | Week 1 | Example overviews, instructor feedback | [Technical Design: System Overview](./Technical_Design.md#1-system-overview) |
| Phase 1 | Project scope & work breakdown | In Progress | Complete WBS, all tasks identified. Instructor feedback: WBS reviewed for completeness. Example: Hardware setup, software environment, data collection. | Week 1 | WBS template, peer review | [Project Management: Implementation Timeline](./Project_Management.md#1-implementation-timeline) |
| Phase 1 | Project completion criteria | Not Started | 1. Accuracy: System detects vehicle speeds within ±5% of manual tools. 2. Cost-Effectiveness: At least 50% lower cost than traditional systems. 3. Reliability: Consistent operation under varied conditions. 4. Data Quality: Accurate, analyzable data logged. 5. Community Impact: Positive feedback and measurable safety improvements. Peer/instructor feedback: Criteria reviewed and accepted. | Week 2 | Example criteria, instructor rubric | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 1 | Assumptions and constraints | In Progress | Assumptions: Affordable/reliable components available; seamless integration; technical expertise available; community support; internet access. Constraints: Budget, timeline, resources, environmental conditions, regulatory compliance. Peer review: Constraints validated by team. | Week 2 | Example lists, peer review | [Technical Design: System Overview](./Technical_Design.md#1-system-overview) |
| Phase 1 | Risk management plan | In Progress | Risks: Sensor accuracy, hardware incompatibility, algorithm performance, data loss, unauthorized access, privacy, budget, legal/IP compliance. Mitigation: Testing, backups, encryption, clear communication, budget monitoring, legal review. Instructor feedback: Plan reviewed and approved. | Week 2 | Risk matrix template, instructor feedback | [Project Management: Risk Management Matrix](./Project_Management.md#3-risk-management-matrix--contingency-planning) |
| Phase 1 | Change control log | Not Started | Track all changes/decisions. Example: Documenting all major project changes and rationale. | Week 2 | Change log template | [Documentation TODO: Outstanding Tasks](./Documentation_TODO.md#1-outstanding-tasks) |
| Phase 1 | Roles and responsibilities | In Progress | All team roles defined. Peer review: Team confirmed role assignments. Example: Hardware lead, software lead, documentation lead. | Week 2 | Team roster, peer review | [Project Management: Executive Summary](./Project_Management.md#executive-summary) |
| Phase 1 | Project schedule & milestones | In Progress | Realistic, buffer time included. Instructor feedback: Timeline reviewed for feasibility. Example: Hardware setup in Week 2, software environment in Week 2. | Week 2 | Gantt chart tool, instructor review | [Project Management: Implementation Timeline](./Project_Management.md#1-implementation-timeline) |
| Phase 1 | Cost estimate | Not Started | All costs accounted for. Example: Hardware, software, cloud, and labor costs itemized. Peer review: Cost table checked for accuracy. | Week 2 | Cost table template, peer review | [Project Management: Budget & Cost Estimates](./Project_Management.md#2-budget--cost-estimates) |
| Phase 1 | Issues log | Not Started | Ongoing issue tracking. Example: Log of technical blockers, resource delays, and resolutions. | Week 2 | Issue tracker tool | [Documentation TODO: Outstanding Tasks](./Documentation_TODO.md#1-outstanding-tasks) |

## Milestone 2: Architectural Design

| Phase | Component | Current Status | Requirements for Desired Performance (with Feedback & Examples) | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 2 | Design planning summary | Not Started | Overview, rationale, issues addressed. Peer/instructor feedback: Context and goals reviewed for clarity. Example: System context diagram, design goals table. | Week 3 | Design summary template, instructor review | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 2 | High-level design (narrative, mockups, flowcharts) | In Progress | All major flows and UI mocked. Peer review: Mockups validated by team. Example: UI wireframes, flowcharts for data pipeline. | Week 3 | Mockup tools, peer review | [Technical Design: System Architecture](./Technical_Design.md#2-system-architecture) |
| Phase 2 | Detailed solution architecture (UML, ERD, workflows) | In Progress | All diagrams complete and accurate. Peer/instructor feedback: Diagrams checked for completeness. Example: UML class diagram, ERD for database. | Week 4 | Diagram tools, instructor feedback | [Technical Design: Table of Contents](./Technical_Design.md#table-of-contents) |
| Phase 2 | Collaboration/sequence diagrams | Not Started | All key interactions diagrammed. Peer review: Sequence diagrams validated by team. Example: Collaboration diagram for sensor-to-database flow. | Week 4 | Diagram tools, peer review | [Technical Design: Sequence Diagram](./Technical_Design.md#5-sequence-diagram-typical-event-flow) |
| Phase 2 | Algorithm descriptions & performance analysis | In Progress | All core algorithms described, with detailed performance analysis and metrics. Instructor feedback: Algorithm selection justified. Example: YOLOv8 for detection, SORT for tracking. | Week 4 | Algorithm documentation, instructor review | [Technical Design: Top-Down Approach](./Technical_Design.md#2x-top-down-approach) |
| Phase 2 | Detailed specs for screens, interfaces, integration | In Progress | All specs documented. Peer review: Specs checked for completeness. Example: API endpoint specs, UI screen specs. | Week 4 | Spec templates, peer review | [Technical Design: Detailed Specs](./Technical_Design.md#detailed-specs-for-screens-interfaces-integration) |
| Phase 2 | Packages, libraries, hardware/software listed | In Progress | All dependencies listed. Peer/instructor feedback: List checked for accuracy. Example: TensorFlow, OpenCV, Flask, Raspberry Pi 5, Sony IMX500. | Week 4 | Inventory list, instructor review | [Technical Design: Packages, Libraries, Hardware/Software](./Technical_Design.md#packages-libraries-hardwaresoftware) |
| Phase 2 | Security approach and resources | In Progress | Security plan documented. Peer/instructor feedback: Plan reviewed for completeness. Example: Use of HTTPS, VPN, audit logs, encryption libraries. | Week 4 | Security checklist, instructor review | [Technical Design: Security/Data Flow Diagram](./Technical_Design.md#9-securitydata-flow-diagram) |

## Milestone 3: Implementation

| Phase | Component | Current Status | Requirements for Desired Performance (with Feedback & Examples) | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 3 | Mapping of requirements to modules/functions | Not Started | All requirements mapped. Peer/instructor feedback: Mapping reviewed for completeness. Example: Table mapping each requirement to a function/module. | Week 5 | Mapping template, instructor review | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 3 | Source code listing & class/file descriptions | In Progress | All code documented. Peer review: Code comments and structure validated by team. Example: Python docstrings, class diagrams. | Week 6 | Codebase, peer review | [Technical Design: Component Interaction Diagram](./Technical_Design.md#4-component-interaction-diagram) |
| Phase 3 | Implementation plan (deployment, integration) | In Progress | All steps clear and testable. Instructor feedback: Plan reviewed for clarity. Example: Step-by-step deployment instructions, integration checklist. | Week 6 | Deployment plan template, instructor review | [Implementation_Deployment.md](./Implementation_Deployment.md) |
| Phase 3 | Requirements review and updates | Not Started | All changes tracked. Peer/instructor feedback: Review summary included. Example: Table of code review comments and actions taken. | Week 6 | Review log, instructor feedback | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |

## Milestone 4: Performance Analysis & Presentation

| Phase | Component | Current Status | Requirements for Desired Performance (with Feedback & Examples) | Completion Date | Resources Needed | Reference Link |
|-------|-----------|---------------|--------------------------------------|-----------------|------------------|---------------|
| Phase 4 | Testing process document (test cases, results) | In Progress | All modules tested, results logged. Peer/instructor feedback: Test cases reviewed for coverage. Example: Table of test cases and results. | Week 7 | Test plan template, instructor review | [Project Management: Quality Assurance & Testing Protocols](./Project_Management.md#4-quality-assurance--testing-protocols) |
| Phase 4 | Requirements testing (mapping to test scenarios) | Not Started | All requirements tested. Peer review: Mapping validated by team. Example: Matrix mapping requirements to test scenarios. | Week 7 | Mapping template, peer review | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 4 | System testing (end-to-end, data flows) | In Progress | All flows tested. Instructor feedback: System test plan reviewed. Example: End-to-end test scripts, data flow diagrams. | Week 7 | Test scripts, instructor review | [Project Management: Quality Assurance & Testing Protocols](./Project_Management.md#4-quality-assurance--testing-protocols) |
| Phase 4 | Operation & maintenance docs (user/admin guide) | In Progress | All guides complete. Peer/instructor feedback: Guides reviewed for clarity. Example: User guide, admin guide, troubleshooting section. | Week 7 | Guide templates, instructor review | [User Guide](./User_Guide.md) |
| Phase 4 | Project completion (final code, docs, video) | Not Started | All deliverables ready. Peer/instructor feedback: Deliverables checklist reviewed. Example: Final codebase, documentation, screencast. | Week 8 | Submission checklist, instructor review | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 4 | Evaluation (milestone review, improvements) | Not Started | All gaps identified. Peer/instructor feedback: Review summary included. Example: Table of identified gaps and improvements. | Week 8 | Review log, instructor feedback | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |
| Phase 4 | Final project submission (code, docs, README, video) | Not Started | All files submitted. Peer/instructor feedback: Submission confirmed. Example: GitHub repo, README, video link. | Week 8 | Submission portal, instructor confirmation | [Documentation TODO: Capstone Requirements Checklist](./Documentation_TODO.md#capstone-requirements-checklist-computer-science) |

## Academic Integrity & References

| Component | Current Status | Requirements for Desired Performance | Completion Date | Resources Needed |
|-----------|---------------|--------------------------------------|-----------------|------------------|
| Academic integrity & plagiarism policy | Ongoing | All work original or cited | Ongoing |  |
| References and sources cited | Ongoing | All sources properly cited | Ongoing |  |

## Glossary

- **YOLOv8**: You Only Look Once, version 8 - a machine learning model for object detection
- **SORT/DeepSORT**: Simple Online and Realtime Tracking algorithms for object tracking
- **Sensor Fusion**: Combining data from multiple sensors to improve accuracy
- **FFT (Fast Fourier Transform)**: Algorithm to convert time-based data to frequency domain for analysis
- **WBS**: Work Breakdown Structure
- **ERD**: Entity-Relationship Diagram
- **UML**: Unified Modeling Language
- **MVP**: Minimal Viable Product
