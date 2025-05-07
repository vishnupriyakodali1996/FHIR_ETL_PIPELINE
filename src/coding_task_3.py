import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
Base_hermes_url = "http://159.65.173.51:8080/v1/snomed/concepts"
primary_care_EHR = "http://137.184.71.65:8080/fhir"


def get_access_token_from_file():
    file_path = Path(data_dir / "access_token.json")
    if not file_path.exists():
        print("Error: access_token.json file not found.")
        return None
    try:
        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
            access_token = json_data.get("access_token")
        return access_token
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading access token from file: {e}")
        return None


def get_headers():
    access_token = get_access_token_from_file()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    return headers

#read new patient ID from patient_id.txt
def load_patient_id_from_file():
    try:
        with open(data_dir / "patient_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: patient_id.txt not found.")
        return None

def select_blood_pressure_observation(patient_resource_id):

    url = f"{BASE_URL}/Observation?patient={patient_resource_id}"
    headers = get_headers()
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "entry" in data and len(data["entry"]) > 0:
            print(f"Total observations found for patient {patient_resource_id}: {len(data['entry'])}")
            # Loop through the observations and check for blood pressure
            for entry in data["entry"]:
                observation = entry.get("resource", {})
                coding = observation.get("code", {}).get("coding", [])
                for code in coding:
                    if code.get("code") in ["85354-9"]:  # LOINC code for blood pressure panel
                        print("Blood pressure observation found:")
                        pprint(observation)
                        return observation
            print(f"No blood pressure observation found for patient {patient_resource_id}.")
        else:
            print(f"No observations found for patient {patient_resource_id}.")
        return None
    except requests.exceptions.RequestException as e:
        print(None)

def create_blood_pressure_observation(patient_id):
    return {
        "resourceType": "Observation",
        "id": "blood-pressure",
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel with all children optional"
            }],
            "text": "Blood pressure systolic & diastolic"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": "2025-05-07",
        "bodySite": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "368209003",
                "display": "Right arm"
            }]
        },
        "component": [
            {
                "code": {
                    "coding": [
                        {"system": "http://loinc.org",
                         "code": "8480-6"}
                    ]
                },
                "valueQuantity": {
                    "value": 140,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                },
                "interpretation": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "H",
                        "display": "Above normal"
                    }],
                    "text": "Normal"
                }]
            },
            {
                "code": {
                    "coding": [
                        {"system": "http://loinc.org",
                         "code": "8462-4" }
                    ]
                },
                "valueQuantity": {
                    "value": 90,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                },
                "interpretation": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "H",
                        "display": "High"
                    }],
                    "text": "Above normal"
                }]
            }
        ]
    }

def post_observation_to_primary_care_ehr(observation):
    url = f"{primary_care_EHR}/Observation"
    headers = {"Content-Type": "application/fhir+json"}
    try:
        response = requests.post(url, headers=headers, json=observation)
        response.raise_for_status()
        print("Observation posted successfully.")
        resp = response.json()
        pprint(resp)
        observation_id = resp.get("id")
        if observation_id:
            with open(data_dir / "observation_id.txt", "w") as f:
                f.write(observation_id)
            print("Observation ID saved to observation_id.txt")
    except requests.exceptions.RequestException as e:
        print(f"Error posting observation: {e}")
        if response is not None:
            print(response.text)

# Getting observation from primary care EHR
def get_EHR_observation():
    with open(data_dir / "observation_id.txt", "r") as f:
        observation_id = f.read().strip()
    url = f'{primary_care_EHR}/Observation/{observation_id}'
    response = requests.get(url=url)
    print(response.url)
    pprint(response.json())

if __name__ == '__main__':
    patient_id = load_patient_id_from_file()
    observation = create_blood_pressure_observation(patient_id)
    post_observation_to_primary_care_ehr(observation)
    get_EHR_observation()
