[Home](index.md) | [ETL](etl_pipeline.md) | [BPMN](BPMN.md) | [Insights](insights.md) | [Team](team_contb.md) | [About](About.md)

# ETL Documentation

This page explains how we extracted patient and condition data from the OpenEMR FHIR API, transformed it using SNOMED parent and child concepts, and loaded it into the Primary Care EHR system. Each coding task is described below.

---

## Task 1 – Parent Concept

- Retrieved a patient from OpenEMR using filters such as name and gender.

```python
snourl = f'{BASE_URL}/Patient?name={name_string}' #by name
url = f'{BASE_URL}/Patient?name={name_string}&gender={gender}' #by name and gender
url = f'{BASE_URL}/Patient?birthdate={bday}' #by birthday
url = f'{BASE_URL}/Condition?patient={patient_resource_id}'#condition
```

- Extracted the patient's conditions and selected one SNOMED CT condition code.

```python
    # Extract SNOMED code
    code = entry['code']['coding'][0]['code']
    display = entry['code']['coding'][0]['display']
```

- Queried Hermes Terminology Server to retrieve the **parent concept**.

```python
    # Fetch SNOMED parent
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=>!{code}'
    snomed_response = requests.get(snomed_url)
```

- Transformed the `Condition` as necessary- Including addressing errors during validation
```python
    str_def_url_pt= "http://example.org/StructureDefinition/my-patient-profile" # URL for validation
    # Removing patient identifier: SSN
    for i in range(len(data.get("identifier", []))):
        if "us-ssn" in data["identifier"][i].get("system", ""):
            data["identifier"].pop(i)
            break
    # Adding district
    data["address"][0]["district"] = "Not found"
    # Creating  the 'text' field in address
    address["text"] = f"{line} {city}, {state}, {postal}"
```
- Created a new `Patient` and `Condition` resource in Primary Care EHR and posted both.

```python
    with open(data_dir / f"{file_name}.json") as f:
        resource = json.load(f)
    response = requests.post(
        f"{FHIR_SERVER_URL}/{resource_type}",
        headers={"Content-Type": "application/fhir+json"},
        json=resource
    )
```

## Task 2 – Child Concept

- Reused the same patient and original SNOMED condition.

```python
    # Fetch SNOMED child
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=<{code}'
    snomed_response = requests.get(snomed_url)
```
- Transforming the data

```python
    # Getting body site for child condition from SNOMED
    snomed_url = (f'{BASE_HERMES_URL}/concepts/{ch_concept_id}/properties?expand=0&format=id:syn')
    snomed_resp = requests.get(snomed_url)
    finding_site_data = snomed_resp.json()
    finding_site = finding_site_data['1'].get('363698007:Finding site')
    find_site_code = finding_site.split(":")[0]
    find_site_name = finding_site.split(":")[1]

    # Fetch severity from snomed
    severity_url = (f'{BASE_HERMES_URL}/search?s="moderate severity"')
    resp= requests.get(severity_url)
    severity_data= resp.json()
    severity_id= str(severity_data[0].get('conceptId'))
    severity_term= severity_data[0].get('preferredTerm')

    # Fetch diagnosis from snomed
    diagnosis_url = (f'{BASE_HERMES_URL}/search?s="diagnosis"')
    resp_diag = requests.get(diagnosis_url)
    dianosis_data = resp_diag.json()
    diagnosis_id= str(dianosis_data[0].get('conceptId'))
    diagnosis_term= dianosis_data[0].get('preferredTerm')
```

- Posted the new Condition to Primary Care EHR.

```python
def post_condition(file_name: str, resource_type: str):
    with open(data_dir / f"{file_name}.json") as f:
        resource = json.load(f)
    with open(data_dir / "patient_id.txt", "r") as f:
        patient_id = f.read().strip()
    resource["subject"]["reference"] = f"Patient/{patient_id}"
    response = requests.post(
        f"{FHIR_SERVER_URL}/{resource_type}",
        headers={"Content-Type": "application/fhir+json"},
        json=resource
    )
```

## Task 3 – Observation

Checked OpenEMR for any blood pressure observation for the patient 

```python
# Loop through the observations and check for blood pressure
            for entry in data["entry"]:
                observation = entry.get("resource", {})
                coding = observation.get("code", {}).get("coding", [])
                for code in coding:
                    if code.get("code") in ["85354-9"]:  # LOINC code for blood pressure panel
                        print("Blood pressure observation found:")
```
Created a blood pressure observation using the following sample structure: [link](https://www.hl7.org/fhir/observation-example.json.html)
```python
"subject": {
            "reference": f"Patient/{patient_id}"

"valueQuantity": {
                    "value": 140,
                    "unit": "mmHg",
```
Posted the Observation to the Primary Care EHR linked to the same patient

```python
blood_observation["subject"] = {
    "reference": f"Patient/{primary_care_patient_id}"
}
post_observation_to_primary_care_ehr(blood_observation, primary_care_EHR, data_dir)
```

## Task 4 – Procedure

Loading Observation to link with Procedure
```python
def load_observation_id_from_file():
    try:
        with open(data_dir / "observation_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: observation_id.txt not found.")
        return None
```
Created a new Procedure resource (SNOMED: 185389009 – Electrocardiographic procedure).

```python
"coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "185389009",
                    "display": "Electrocardiographic procedure"
                }
            ],
```

Posted the resource to Primary Care EHR.

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

Loaded the Patient and Condition resources from local JSON files and extracted necessary information
```python
    with open(data_dir / "patient.json") as f:
        patient_data = json.load(f)

    with open(data_dir / "condition.json") as f:
        condition_data = json.load(f)
``` 
Queried Hermes to map SNOMED code to ICD-10 using map/447562003.
```python
# Fetch ICD-10 mapping
    map_url = f"{BASE_HERMES_URL}/{condition_code}/map/447562003"
```
Constructed an HL7 v2 ADT^A01 message using the hl7apy library.

```python
from hl7apy.core import Message
msg = Message("ADT_A01")
msg.pid.pid_11 = f"{address}^{city}^{state}^{zip_code}^^H"
msg.dg1.dg1_3 = f"{icd_code}^{icd_display}^I10" # DG1 Segment with ICD Code
```

Saved the message to hl7_message.txt.

## Validation

Validation was run using the validate.py script to confirm conformance with FHIR structure definitions.

```python
 f"{FHIR_SERVER_URL}/{resource_type}/$validate",
```

