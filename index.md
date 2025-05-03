[Home](index.md) | [ETL](etl_pipeline.md) | [BPMN](BPMN.md) | [Insights](insights.md) | [Team](team_contb.md) | [About](About.md)

# Final Project – ETL Pipeline Using FHIR APIs

Welcome to our Group 5 project website. This project showcases our ability to build an end-to-end ETL (Extract, Transform, Load) pipeline for healthcare data using real-world FHIR APIs and HL7 standards.

---

##  Project Overview

We designed and executed a full ETL pipeline to:
- Extract patient data and conditions from the OpenEMR FHIR API
- Transform SNOMED codes using parent/child relationships from Hermes Terminology Server
- Load structured resources into a target Primary Care EHR FHIR server
- Generate HL7 v2 messages for legacy system compatibility

---

## Technologies Used

- **Python** – Main programming language for all scripts
- **FHIR APIs** – OpenEMR, Primary Care EHR
- **Hermes Terminology Server** – For SNOMED concept transformations and ICD mapping
- **hl7apy** – For HL7 v2 message creation
- **GitHub & GitHub Pages** – Version control and documentation hosting

---

## Deliverables

- 5 completed coding tasks (detailed on the ETL page)
- FHIR resource validation using meta.profile
- HL7 message export from FHIR
- Simple data visualizations
- Full project documentation on this site

Use the links above to explore each section of our project.
