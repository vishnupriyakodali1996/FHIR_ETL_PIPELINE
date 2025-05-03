[Home](index.md) | [ETL](etl_pipeline.md) | [BPMN](BPMN.md) | [Insights](insights.md) | [Team](team_contb.md) | [About](About.md)

# ETL Documentation

This page explains how we extracted patient and condition data from the OpenEMR FHIR API, transformed it using SNOMED parent and child concepts, and loaded it into the Primary Care EHR system. Each coding task is described below.

## Task 1 – Parent Concept

- We searched for a patient using name filters and retrieved their condition data.
- From the condition, we extracted the SNOMED code.
- We used the Hermes Terminology Server to get the parent SNOMED concept.
- We updated the Condition resource with the parent concept and added a `meta.profile`.
- Then we posted the patient and this condition to the Primary Care EHR server.

## Task 2 – Child Concept

- We used the same patient and original SNOMED condition.
- Using Hermes, we retrieved a child SNOMED concept for that condition.
- We created a new Condition resource using the child concept and added the profile.
- We posted this second Condition to the Primary Care EHR server as well.

## Task 3 – Observation

- We checked if the patient had any Observation resources in OpenEMR.
- If a blood pressure observation was found, we extracted and saved it.
- We updated the subject reference to match the new patient ID in Primary Care EHR.
- Then we posted the Observation to the Primary Care EHR server.

## Task 4 – Procedure

- We created a Procedure resource based on a template.
- We linked the Procedure to both the patient and the Observation using references.
- The resource was then posted to the Primary Care EHR server.

## Task 5 – HL7 Message

- We loaded the posted Patient and Condition resources from local files.
- We used Hermes to map the SNOMED code to an ICD-10 code.
- Using the `hl7apy` library, we generated an HL7 v2 ADT message.
- The message included segments like MSH, PID, PV1, and DG1, and was saved to a text file.

## Validation

Each resource (Patient and both Conditions) was validated using the appropriate `meta.profile` value before being posted. This ensured conformance to the required FHIR structure.

