import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

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

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
Base_hermes_url = "http://159.65.173.51:8080/v1/snomed/concepts"
primary_care_EHR = "http://137.184.71.65:8080/fhir/Patient"
FHIR_SERVER_URL = "http://137.184.71.65:8080/fhir"

# looking for one patient resource based on resource ID
def get_fhir_patient(resource_id):
    url = f'{BASE_URL}/Patient/{resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())
    print('------------------------------------------------------------- 2')

# Search for all the conditions of this patient.
def search_all_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    #pprint(data)
    print(f"Total num of conditions for patient: {len(data['entry'])}")
    num = 0
    for items in data['entry']:
        for dicts in items.get('resource')['code']['coding']:
            code = dicts.get('code')
            condition = dicts.get('display')
            num = num + 1
            print(f"Condition ({num}) - code: {code} - condition: {condition}")

    print('------------------------------------------------------------- 6')

# Get any one condition of this patient
def get_one_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    #pprint(data)
    nice_entry = data['entry'][16]
    #pprint(nice_entry)
    resource = nice_entry.get('resource')
    code_section = resource.get('code')
    codings = code_section.get('coding')
    for coding in codings:
        code = coding.get('code')
        display = coding.get('display')
        print(f"{code} is the concept ID for Condition: {display}")
    print('------------------------------------------------------------- 7')

# Get concept ID for the condition
def get_concept_id(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    first_entry = data['entry'][16]
    resource = first_entry.get('resource')
    code_section = resource.get('code')
    codings = code_section.get('coding')
    for coding in codings:
        code = coding.get('code')
        display = coding.get('display')
        print(f"{code} is the concept ID for Condition: {display}")


# Get parent term for the condition of the patient
BASE_HERMES_URL = 'http://159.65.173.51:8080/v1/snomed'


def get_child(patient_resource_id):
    # Fetch condition from FHIR server
    condition_url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=condition_url, headers=get_headers())
    print(response.url)
    #pprint(response.json())
    pprint(response.json()['entry'][16])
    entry = response.json()['entry'][16]['resource']
    # Extract SNOMED code
    code = entry['code']['coding'][0]['code']
    display = entry['code']['coding'][0]['display']
    print(f'Condition code: {code}, display: {display}')

    # Fetch SNOMED parent
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=<!{code}'
    snomed_response = requests.get(snomed_url)
    print(snomed_response.url)
    #pprint(snomed_response.json())
    data= snomed_response.json()
    ch_concept_id= data[1]["conceptId"]
    ch_pref_term= data[1]["preferredTerm"]
    print(f"Child SNOMED condition for {code} is {ch_pref_term} and concept is {ch_concept_id}")
    print("-------------------------------------------------------------------------------------")

def create_child_condition_json(patient_resource_id):
    # Get original condition
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    condition = data['entry'][16]['resource']

    # Extract original SNOMED code
    original_code = condition['code']['coding'][0]['code']

    # Fetch SNOMED parent
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=<!{original_code}'
    snomed_response = requests.get(snomed_url)
    print(snomed_response.url)
    # pprint(snomed_response.json())
    data = snomed_response.json()
    ch_concept_id = data[1]["conceptId"]
    ch_pref_term = data[1]["preferredTerm"]
    # Replace code and display
    condition['code']['coding'][0]['code'] = str(ch_concept_id)
    condition['code']['coding'][0]['display'] = ch_pref_term
    condition['code']['text'] = ch_pref_term  # optional but helpful
    # Save to new file
    with open(data_dir / "child_condition.json", "w") as f:
        json.dump(condition, f, indent=2)


if __name__ == '__main__':
    print('-------------------------------------------------------------')
    #get_fhir_patient(resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_one_condition(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_child(patient_resource_id= '985ac812-ddd2-49ce-9806-160e27d7cfa7')
    create_child_condition_json(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')