import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
primary_care_EHR = "http://137.184.71.65:8080/fhir"


def get_access_token_from_file():
    file_path = Path(data_dir / "access_token.json")
    if not file_path.exists():
        print("Error: access_token.json file not found.")
        return None
    try:
        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
            return json_data.get("access_token")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading access token: {e}")
        return None


def get_headers():
    token = get_access_token_from_file()
    return {"Authorization": f"Bearer {token}"}


def load_patient_id_from_file():
    try:
        with open(data_dir / "patient_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: patient_id.txt not found.")
        return None


def load_observation_id_from_file():
    try:
        with open(data_dir / "observation_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: observation_id.txt not found.")
        return None


def build_procedure_resource(patient_id, observation_id):
    return {
        "resourceType": "Procedure",
        "status": "completed",
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "185389009",
                    "display": "Electrocardiographic procedure"
                }
            ],
            "text": "Electrocardiographic procedure"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "performedDateTime": "2024-12-01T10:30:00Z",
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/procedure-observation",
                "valueReference": {
                    "reference": f"Observation/{observation_id}"
                }
            }
        ]
    }


def save_procedure_to_file(procedure, patient_id):
    file_path = data_dir / f"procedure_{patient_id}.json"
    with open(file_path, "w") as f:
        json.dump(procedure, f, indent=2)
    print(f"Procedure saved to {file_path}")


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


if __name__ == '__main__':
    patient_id = load_patient_id_from_file()
    observation_id = load_observation_id_from_file()

    if not patient_id or not observation_id:
        print("Missing patient or observation ID. Aborting.")
        exit()

    procedure = build_procedure_resource(patient_id, observation_id)
    save_procedure_to_file(procedure, patient_id)
    post_procedure_to_primary_care_ehr(procedure)
