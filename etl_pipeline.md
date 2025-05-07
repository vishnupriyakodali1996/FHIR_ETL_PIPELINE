[Home](index.md) | [ETL](etl_pipeline.md) | [BPMN](BPMN.md) | [Insights](insights.md) | [Team](team_contb.md) | [About](About.md)

# ETL Documentation

This page explains how we extracted patient and condition data from the OpenEMR FHIR API, transformed it using SNOMED parent and child concepts, and loaded it into the Primary Care EHR system. Each coding task is described below.

---

## Task 1 – Parent Concept

- Retrieved a patient from OpenEMR using filters such as name and gender.
- Extracted the patient's conditions and selected one SNOMED CT condition code.
- Queried Hermes Terminology Server to retrieve the **parent concept**.
- Modified the `Condition` resource by replacing the SNOMED code with the parent, and added metadata for validation (`meta.profile`).
- Created a new `Patient` and `Condition` resource in Primary Care EHR and posted both.

**Code Snippet – Fetching Parent Concept from Hermes:**

```python
snomed_url = f'{BASE_HERMES_URL}/search?constraint=>!{code}'
snomed_response = requests.get(snomed_url)
parent_id = snomed_response.json()[0].get('conceptId')
parent_term = snomed_response.json()[0].get('preferredTerm')

post_patient("patient", "Patient")
post_condition("parent_condition", "Condition")
```
## Task 2 – Child Concept

Reused the same patient and original SNOMED condition.
Queried Hermes for a child SNOMED concept.
Created a second Condition using this child code, updated metadata, and added body site and severity using SNOMED properties.
Posted the new Condition to Primary Care EHR.

```python
snomed_url = f'{BASE_HERMES_URL}/search?constraint=<!{original_code}'
snomed_response = requests.get(snomed_url)
ch_concept_id = snomed_response.json()[1]["conceptId"]
ch_pref_term = snomed_response.json()[1]["preferredTerm"]
```


