import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
BASE_HERMES_URL = "http://159.65.173.51:8080/v1/snomed"
PRIMARY_CARE_BASE_URL = "http://137.184.71.65:8080/fhir"

# Patient info to search
FAMILY, GIVEN, BIRTHDATE = "Bailey", "Trudie", "1980-02-21"
NTH_CONDITION = 1  # Get 1st condition


def get_access_token():
    file_path = Path(data_dir / "access_token.json")
    return json.loads(file_path.read_text())["access_token"]


def headers(fhir=True):
    h = {"Authorization": f"Bearer {get_access_token()}"}
    if fhir:
        h["Content-Type"] = "application/fhir+json"
    return h


def search_patient():
    url = f"{BASE_URL}/Patient"
    params = {"family": FAMILY, "given": GIVEN, "birthdate": BIRTHDATE}
    resp = requests.get(url, headers=headers(), params=params)
    resp.raise_for_status()
    data = resp.json()
    return data['entry'][0]['resource']


def get_conditions(patient_id):
    url = f"{BASE_URL}/Condition?patient={patient_id}"
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    return resp.json().get('entry', [])


def get_condition_code(entry):
    coding = entry['resource']['code']['coding'][0]
    return coding['system'], coding['code'], coding['display']


def get_parent_snomed(concept_id):
    url = f"{BASE_HERMES_URL}/concepts/{concept_id}/extended"
    resp = requests.get(url)
    resp.raise_for_status()
    parents = resp.json().get("parents", [])
    if not parents:
        return concept_id, None
    parent = parents[0]
    return parent["conceptId"], parent["pt"]["term"]


def create_patient_in_primary(patient_data):
    patient_data = {
        "resourceType": "Patient",
        "identifier": patient_data.get("identifier", []),
        "name": patient_data.get("name", []),
        "telecom": patient_data.get("telecom", []),
        "gender": patient_data.get("gender"),
        "birthDate": patient_data.get("birthDate"),
        "address": patient_data.get("address", []),
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
        }
    }
    url = f"{PRIMARY_CARE_BASE_URL}/Patient"
    resp = requests.post(url, headers=headers(), json=patient_data)
    resp.raise_for_status()
    created = resp.json()
    print("\nPatient created on Primary Care")
    pprint(created)
    return created, created["id"]


def create_condition_in_primary(patient_id, system, code, display):
    condition = {
        "resourceType": "Condition",
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "coding": [{"system": system, "code": code, "display": display}],
            "text": display
        },
        "clinicalStatus": {"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "active",
            "display": "Active"
        }]},
        "verificationStatus": {"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
            "code": "confirmed",
            "display": "Confirmed"
        }]}
    }
    url = f"{PRIMARY_CARE_BASE_URL}/Condition"
    resp = requests.post(url, headers=headers(), json=condition)
    resp.raise_for_status()
    created = resp.json()
    print("\nCondition created on Primary Care")
    pprint(created)
    return created


def validate_resource(resource, resource_type):
    url = f"{PRIMARY_CARE_BASE_URL}/{resource_type}/$validate"
    resp = requests.post(url, headers=headers(), json=resource)
    print(f"\nValidation result for {resource_type} (HTTP {resp.status_code}):")
    pprint(resp.json())


if __name__ == '__main__':
    try:
        print("Searching for patient...")
        patient = search_patient()

        print("\nGetting patient's conditions...")
        condition_entries = get_conditions(patient["id"])
        if len(condition_entries) < NTH_CONDITION:
            raise ValueError("Not enough conditions for the selected index")

        system, code, display = get_condition_code(condition_entries[NTH_CONDITION - 1])
        print(f"\nSelected Condition: {code} - {display}")

        parent_code, parent_display = get_parent_snomed(code)
        print(f"\nParent SNOMED: {parent_code} - {parent_display or display}")

        print("\nCreating patient on Primary Care...")
        new_patient_resource, new_patient_id = create_patient_in_primary(patient)

        print("\nCreating condition on Primary Care using parent concept...")
        new_condition_resource = create_condition_in_primary(new_patient_id, system, parent_code, parent_display or display)

        print("\nValidating patient and condition resources...")
        validate_resource(new_patient_resource, "Patient")
        validate_resource(new_condition_resource, "Condition")

    except Exception as e:
        print(f"\nERROR: {e}")
