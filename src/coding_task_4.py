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


def check_procedure_in_openemr(patient_resource_id):
    openemr_url = f'{BASE_URL}/Procedure?patient={patient_resource_id}'
    headers = get_headers()
    try:
        response = requests.get(url=openemr_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "entry" in data and len(data["entry"]) > 0:
            print(f"Procedure resource exists for patient {patient_resource_id} in OpenEMR.")
            return True
        else:
            print(f"No Procedure resource found for patient {patient_resource_id} in OpenEMR.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking Procedure in OpenEMR: {e}")
        return False

#Create a Procedure resource for the patient and post it to the Primary Care EHR server.
def create_procedure_resource(patient_resource_id):
    url = f'{primary_care_EHR}/Procedure'
    headers = get_headers()
    headers["Content-Type"] = "application/json"

    # Create the Procedure resource JSON
    procedure_data = {
        "resourceType": "Procedure",
        "status": "completed",
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "80146002",  # Example SNOMED code for a procedure
                    "display": "Appendectomy"
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_resource_id}"
        },
        "performedDateTime": "2025-05-01T10:00:00Z"  # Example date and time
    }

    try:
        response = requests.post(url, headers=headers, json=procedure_data)
        response.raise_for_status()
        print("Procedure resource created successfully in Primary Care EHR.")
        pprint(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error creating Procedure resource: {e}")


# Main execution
if __name__ == '__main__':
    print('-------------------------------------------------------------')
    # Check if Procedure exists in OpenEMR
    if not check_procedure_in_openemr(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7'):
        # Create and post Procedure resource if it does not exist
        create_procedure_resource(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')