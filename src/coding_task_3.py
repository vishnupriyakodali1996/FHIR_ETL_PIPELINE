import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
Base_hermes_url = "http://159.65.173.51:8080/v1/snomed/concepts"
primary_care_EHR = "http://137.184.71.65:8080/fhir"

data_dir = Path("/Users/laurandoigo/PycharmProjects/GROUP_PROJECT/src/data") #replace with your path

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

#read new patient ID from patient_id.txt
def load_patient_id_from_file():
    try:
        with open(data_dir / "patient_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: patient_id.txt not found.")
        return None

def check_observation_in_openemr(patient_resource_id):
    url = f"{BASE_URL}/Observation?patient={patient_resource_id}"
    headers = get_headers()
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        data = response.json()
        #pprint(data)
        if "entry" in data and len(data["entry"]) > 0:
            print(f"Observation resource exists for patient {patient_resource_id} in OpenEMR.")
            return True
        else:
            print(f"No Observation resource found for patient {patient_resource_id} in OpenEMR.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking Observation in OpenEMR: {e}")
        return False

def select_first_observation(patient_resource_id):
    url = f"{BASE_URL}/Observation?patient={patient_resource_id}"
    headers = get_headers()
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "entry" in data and len(data["entry"]) > 0:
            print(f"Total observations found for patient {patient_resource_id}: {len(data['entry'])}")
            # Loop through the observations and select the first one
            for entry in data["entry"]:
                first_observation = entry.get("resource", {})
                print("First observation found:")
                pprint(first_observation)
                return first_observation
        else:
            print(f"No observations found for patient {patient_resource_id}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching observations: {e}")
        return None

# Fetch the first observation and save it using the patient ID from file
def save_first_observation_to_file(patient_resource_id):
    first_observation = select_first_observation(patient_resource_id)
    if first_observation:
        file_path = data_dir / f"first_observation_{load_patient_id_from_file()}.json"
        try:
            with open(file_path, "w") as json_file:
                json.dump(first_observation, json_file, indent=2)
            print(f"First observation saved successfully at: {file_path}")
        except Exception as e:
            print(f"Error saving first observation to file: {e}")
    else:
        print("No observation found to save.")

#Post the observation data to the Primary Care EHR FHIR server.
def post_observation_to_primary_care_ehr(observation_data):
    url = f"{primary_care_EHR}/Observation"
    headers = get_headers()
    try:
        response = requests.post(url=url, headers=headers, json=observation_data)
        response.raise_for_status()
        print("Observation posted successfully to Primary Care EHR.")
        pprint(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error posting observation to Primary Care EHR: {e}")


# Main execution
if __name__ == '__main__':
    patient_resource_id = '985ac812-ddd2-49ce-9806-160e27d7cfa7'
    first_observation = select_first_observation(patient_resource_id)
    print('-------------------------------------------------------------')
    check_observation_in_openemr(patient_resource_id)
    save_first_observation_to_file(patient_resource_id)
    post_observation_to_primary_care_ehr(first_observation)
