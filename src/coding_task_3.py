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
    if not access_token:
        raise ValueError("No access token found.")
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


def check_observation_in_openemr(patient_resource_id):
    url = f"{BASE_URL}/Observation?patient={patient_resource_id}"
    headers = get_headers()
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "entry" in data and len(data["entry"]) > 0:
            print(f"Observation resource exists for patient {patient_resource_id} in OpenEMR.")
            return True
        else:
            print(f"No Observation resource found for patient {patient_resource_id} in OpenEMR.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking Observation in OpenEMR: {e}")
        return False


def create_observation_resource(patient_resource_id):
    url = f"{primary_care_EHR}/Observation"
    headers = get_headers()

    # Example: Body temperature observation
    observation_data = {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8310-5",  # LOINC code for body temperature
                    "display": "Body temperature"
                }
            ],
            "text": "Body temperature"
        },
        "subject": {
            "reference": f"Patient/{patient_resource_id}"
        },
        "effectiveDateTime": "2025-05-01T10:00:00Z",
        "valueQuantity": {
            "value": 37.2,
            "unit": "degrees C",
            "system": "http://unitsofmeasure.org",
            "code": "Cel"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=observation_data)
        response.raise_for_status()
        print("Observation resource created successfully in Primary Care EHR.")
        pprint(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error creating Observation resource: {e}")
        if e.response is not None:
            print("Response content:", e.response.text)


# Main execution
if __name__ == '__main__':
    patient_id = '985ac812-ddd2-49ce-9806-160e27d7cfa7'
    print('-------------------------------------------------------------')
    if not check_observation_in_openemr(patient_id):
        create_observation_resource(patient_id)
