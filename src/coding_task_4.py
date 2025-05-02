import json
import requests
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_EHR = "http://137.184.71.65:8080/fhir"
DATA_DIR = Path(data_dir)

def get_access_token_from_file():
    with open(DATA_DIR / "access_token.json") as f:
        return json.load(f).get("access_token")

def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token_from_file()}",
        "Content-Type": "application/json"
    }

def load_patient_id_from_file():
    with open(DATA_DIR / "patient_id.txt") as f:
        return f.read().strip()

def check_existing_procedures(patient_id):
    url = f"{BASE_URL}/Procedure?patient={patient_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    data = response.json()

    if "entry" in data:
        print(f"Found {len(data['entry'])} Procedure(s) for patient {patient_id}")
        return data["entry"]
    else:
        print(f"No Procedure found for patient {patient_id}")
        return None

def create_sample_procedure(primary_patient_id):
    return {
        "resourceType": "Procedure",
        "status": "completed",
        "code": {
            "coding": [{
                "system": "http://www.ama-assn.org/go/cpt",
                "code": "93000",
                "display": "Electrocardiogram"
            }],
            "text": "Electrocardiogram"
        },
        "subject": {
            "reference": f"Patient/{primary_patient_id}"
        },
        "performedDateTime": "2024-12-01T10:30:00Z"
    }

def post_procedure_to_primary_care(procedure_resource):
    url = f"{PRIMARY_CARE_EHR}/Procedure"
    headers = {"Content-Type": "application/fhir+json"}
    response = requests.post(url, headers=headers, json=procedure_resource)
    response.raise_for_status()

    result = response.json()
    print("Procedure posted successfully.")
    print(json.dumps(result, indent=2))

    with open(DATA_DIR / "new_procedure_template.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    patient_id_openemr = "985ac812-ddd2-49ce-9806-160e27d7cfa7"
    check_existing_procedures(patient_id_openemr)

    primary_care_patient_id = load_patient_id_from_file()
    procedure_resource = create_sample_procedure(primary_care_patient_id)

    post_procedure_to_primary_care(procedure_resource)
