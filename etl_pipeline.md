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

**Fetching Parent Concept from Hermes:**

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

## Task 3 – Observation

Checked OpenEMR for any Observation resources for the patient.
Identified blood pressure (LOINC: 85354-9) and saved it locally.
Updated the subject field to reference the new Primary Care patient.
Posted the Observation to the Primary Care EHR.

```python
blood_observation["subject"] = {
    "reference": f"Patient/{primary_care_patient_id}"
}
post_observation_to_primary_care_ehr(blood_observation, primary_care_EHR, data_dir)
```

## Task 4 – Procedure

Created a new Procedure resource (SNOMED: 185389009 – Electrocardiographic procedure).
Linked this Procedure to the patient and an associated Observation.
Posted the resource to Primary Care EHR.

Linking Observation to Procedure
```python
"extension": [
    {
        "url": "http://hl7.org/fhir/StructureDefinition/procedure-observation",
        "valueReference": {
            "reference": f"Observation/{observation_id}"
        }
    }
]
```
```python
def post_procedure_to_primary_care_ehr(procedure):
    url = f"{primary_care_EHR}/Procedure"
    headers = {"Content-Type": "application/fhir+json"}
    try:
        response = requests.post(url, headers=headers, json=procedure)
        response.raise_for_status()
        print("Procedure posted successfully.")
        resp = response.json()
        pprint(resp)
        procedure_id = resp.get("id")
        if procedure_id:
            with open(data_dir / "procedure_id.txt", "w") as f:
                f.write(procedure_id)
            print(f"Procedure ID saved to procedure_id.txt")
    except requests.exceptions.RequestException as e:
        print(f"Error posting procedure: {e}")
        if response is not None:
            print(response.text)
```


## Task 5 – HL7 ADT Message Generation

Loaded the Patient and Condition resources from local JSON files.
Queried Hermes to map SNOMED code to ICD-10 using map/447562003.
Constructed an HL7 v2 ADT^A01 message using the hl7apy library.
Included MSH, PID, PV1, and DG1 segments.

# Fetch ICD-10 mapping
```python
    map_url = f"{BASE_HERMES_URL}/{condition_code}/map/447562003"
    map_response = requests.get(map_url)
    mapping_data = map_response.json()
    if not mapping_data:
        print(f"No ICD-10 mapping found for SNOMED code {condition_code}")
        raise ValueError(f"No ICD-10 mapping found for SNOMED code {condition_code}")

    mapping = mapping_data[0]
    icd_code = mapping["mapTarget"]
    icd_display = mapping.get("mapTargetName", "ICD-10 Term")

    print(f"{icd_code} is the mapped ICD code for SNOMED code: {condition_code} - {condition_display}")
```

DG1 Segment with ICD Code:
```python
msg.dg1.dg1_3 = f"{icd_code}^{icd_display}^I10"
msg.dg1.dg1_4 = condition_display
```
Saved the message to hl7_message.txt.

## Validation

For Tasks 1 and 2, the Patient and both Condition resources included the appropriate meta.profile fields before posting to ensure schema compliance.
```python
"meta": {
  "profile": [
    "http://example.org/StructureDefinition/my-condition-profile"
  ]
}
Validation was run using the validate.py script to confirm conformance with FHIR structure definitions.
```

