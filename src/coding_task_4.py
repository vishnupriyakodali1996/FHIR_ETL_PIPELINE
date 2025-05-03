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


# Load patient ID from file (if exists)
def load_patient_id_from_file():
    try:
        with open(data_dir / "patient_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: patient_id.txt not found.")
        return None



# Load Observation ID from file (if exists)
def load_observation_id_from_file():
    try:
        with open(data_dir / "observation_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: observation_id.txt not found.")
        return None


# Load procedure template from JSON file
def load_procedure_template():
    try:
        with open(data_dir / "new_procedure_template.json", "r") as file:
            procedure_template = json.load(file)
        return procedure_template
    except FileNotFoundError:
        print("Error: new_procedure_template.json file not found.")
        return None


# Save the procedure to a JSON file
def save_procedure_to_file(procedure, patient_id):
    file_path = data_dir / f"procedure_{patient_id}.json"
    try:
        with open(file_path, "w") as json_file:
            json.dump(procedure, json_file, indent=2)
        print(f"Procedure saved successfully at: {file_path}")
    except Exception as e:
        print(f"Error saving procedure to file: {e}")


# Post the procedure to the Primary Care EHR FHIR server
def post_procedure_to_primary_care_ehr(procedure):
    url = f"{primary_care_EHR}/Procedure"
    headers = {
        "Content-Type": "application/fhir+json"  # Set the correct content type
    }
    try:
        response = requests.post(url=url, headers=headers, json=procedure)
        response.raise_for_status()  # Check for errors in the response
        print("Procedure posted successfully to Primary Care EHR.")
        procedure_response = response.json()
        pprint(procedure_response)

        # Save procedure ID
        procedure_id = procedure_response["id"]
        with open(data_dir / "procedure_id.txt", "w") as f:
            f.write(procedure_id)
        print(f"Procedure ID saved to {data_dir / 'procedure_id.txt'}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting procedure to Primary Care EHR: {e}")
        print(response.text)


# Main execution
if __name__ == '__main__':
    # Load the required IDs and the procedure template
    patient_id = load_patient_id_from_file()
    observation_id = load_observation_id_from_file()
    procedure_template = load_procedure_template()

    # Update procedure template with patient and observation references
    procedure_template["subject"]["reference"] = f"Patient/{patient_id}"
    procedure_template["extension"] = [
        {
            "url": "http://hl7.org/fhir/StructureDefinition/procedure-observation",
            "valueReference": {
                "reference": f"Observation/{observation_id}"
            }
        }
    ]

    # Save the procedure as a JSON file
    save_procedure_to_file(procedure_template, patient_id)

    # Post the procedure to the FHIR server
    post_procedure_to_primary_care_ehr(procedure_template)

