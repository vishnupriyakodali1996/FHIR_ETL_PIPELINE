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
        print(f"Error fetching observations: {e}")
        return None

#Fetch the blood observation and save it using the patient ID from file
def save_blood_pressure_observation_to_file(patient_resource_id):
    blood_observation = select_blood_pressure_observation(patient_resource_id)
    if blood_observation:
        file_path = data_dir / f"blood_observation_{load_patient_id_from_file()}.json"
        try:
            with open(file_path, "w") as json_file:
                json.dump(blood_observation, json_file, indent=2)
            print(f"Blood pressure observation saved successfully at: {file_path}")
        except Exception as e:
            print(f"Error saving blood pressure observation to file: {e}")
    else:
        print("No blood pressure observation found to save.")


# Post the observation to the Primary Care EHR FHIR server
import requests
from pathlib import Path

def post_observation_to_primary_care_ehr(blood_observation, primary_care_EHR, data_dir):
    url = f"{primary_care_EHR}/Observation"
    headers = {
        "Content-Type": "application/fhir+json"
    }

    try:
        response = requests.post(url=url, headers=headers, json=blood_observation)
        response.raise_for_status()
        print("Observation posted successfully to Primary Care EHR.")
        observation_response = response.json()
        #pprint(observation_response)

        # Save observation ID
        observation_id = observation_response.get("id")
        if observation_id:
            data_dir = Path(data_dir)  # Ensure it's a Path object
            file_path = data_dir / "observation_id.txt"
            with open(file_path, "w") as f:
                f.write(observation_id)
            print(f"Observation ID saved to {file_path}")
        else:
            print("No observation ID returned in response.")

    except requests.exceptions.RequestException as e:
        print(f"Error posting observation to Primary Care EHR: {e}")
        if 'response' in locals() and response is not None:
            print(response.text)

# Main execution
if __name__ == '__main__':
    patient_resource_id = '985ac812-ddd2-49ce-9806-160e27d7cfa7'

    # Fetch the blood pressure observation
    blood_observation = select_blood_pressure_observation(patient_resource_id)
    print('-------------------------------------------------------------')

    # Check if the observation exists in OpenEMR
    check_observation_in_openemr(patient_resource_id)

    # Save the blood pressure observation to a file
    save_blood_pressure_observation_to_file(patient_resource_id)

    # Read Primary Care EHR patient ID
    primary_care_patient_id = load_patient_id_from_file()
    if not primary_care_patient_id:
        print("Aborting: No valid patient ID for Primary Care EHR.")
        exit()

    # Replace the subject reference to match Primary Care EHR patient
    if blood_observation:
        blood_observation["subject"] = {
            "reference": f"Patient/{primary_care_patient_id}"
        }
        print(f"Updated observation subject to Primary Care EHR Patient/{primary_care_patient_id}")

        # Post to Primary Care EHR
        post_observation_to_primary_care_ehr(blood_observation, primary_care_EHR, data_dir)
    else:
        print("Aborting: No observation to post.")

