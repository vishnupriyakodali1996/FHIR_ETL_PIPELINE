import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
Base_hermes_url = "http://159.65.173.51:8080/v1/snomed/concepts"
primary_care_EHR = "http://137.184.71.65:8080/fhir/Patient"
FHIR_SERVER_URL = "http://137.184.71.65:8080/fhir"

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


#To know all the resources in FHIR data
def get_all_resources():
    url = f"{BASE_URL}/metadata"
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    for rest in data["rest"]:
        for resource in rest["resource"]:
            print(resource["type"])
    print('------------------------------------------------------------- 1')


#looking for one patient resource based on resource ID
def get_fhir_patient(resource_id):
    url = f'{BASE_URL}/Patient/{resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())
    print('------------------------------------------------------------- 2')


# Search patient by name
def search_patient_by_name(name_string):
    url = f'{BASE_URL}/Patient?name={name_string}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data= (response.json())
    if 'entry' in data:
        entry = data['entry']
        for item in entry:
            resource_id = item['resource']['id']
            given_name = f"{item['resource']['name'][0]['given'][0]}"
            family_name = f"{item['resource']['name'][0]['family']}"
            print(f"Patient name: {given_name} {family_name}\n Resource ID: {resource_id}")
    else:
        print('No results found')
    print('------------------------------------------------------------- 3')

# Search patient by name and gender
def search_patient_by_name_gender(name_string, gender):
    url = f'{BASE_URL}/Patient?name={name_string}&gender={gender}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    if 'entry' in data:
        entry = data['entry']
        for item in entry:
            resource_id = item['resource']['id']
            given_name = f"{item['resource']['name'][0]['given'][0]}"
            family_name = f"{item['resource']['name'][0]['family']}"
            print(f"{resource_id} - {item['resource']['gender']} - {given_name} {family_name}")
    else:
        print('No results found')
        print('------------------------------------------------------------- 4')

# Search patient by birthday
def search_patient_by_bday(bday):
    url = f'{BASE_URL}/Patient?birthdate={bday}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data= (response.json())
    print(f"Patient details with date of birth {bday}")
    if 'entry' in data:
        print(f"Number of entries: {len(data['entry'])}")
        entry = data['entry']
        for item in entry:
            resource_id = item['resource']['id']
            date_of_birth= item['resource']['birthDate']
            given_name = f"{item['resource']['name'][0]['given'][0]}"
            family_name = f"{item['resource']['name'][0]['family']}"
            gender = f"{item['resource']['gender']}"
            print(f"Name of patient:{given_name} {family_name}\nGender: {gender} \nResource ID: {resource_id}\nDate of birth:{date_of_birth}")
    else:
        print('No results found')
    print('------------------------------------------------------------- 5')

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
        print(f"Patient has Condition: {display}")
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
    print('------------------------------------------------------------- 8')

# Get parent term for the condition of the patient
BASE_HERMES_URL = 'http://159.65.173.51:8080/v1/snomed'


def get_parent(patient_resource_id):
    # Fetch condition from FHIR server
    condition_url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=condition_url, headers=get_headers())
    print(response.url)

    entry = response.json()['entry'][16]['resource']
    # Extract SNOMED code
    code = entry['code']['coding'][0]['code']
    display = entry['code']['coding'][0]['display']
    print(f'Condition code: {code}, display: {display}')

    # Fetch SNOMED parent
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=>!{code}'
    snomed_response = requests.get(snomed_url)
    print(snomed_response.url)
    pprint(snomed_response.json())
    parent_id = snomed_response.json()[0].get('conceptId')
    print(f'The parent concept for condition is: {parent_id}')
    print('------------------------------------------------------------- 9')

def create_patient_json(resource_id):
    url = f'{BASE_URL}/Patient/{resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data=response.json()
    with open(data_dir / "patient.json", "w") as f:
        json.dump(data, f, indent=2)
    print('------------------------------------------------------------- 10')

def create_condition_json(patient_resource_id):
    # Get original condition
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    condition = data['entry'][16]['resource']

    # Extract original SNOMED code
    original_code = condition['code']['coding'][0]['code']

    # Get parent SNOMED concept from Hermes
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=>!{original_code}'
    snomed_response = requests.get(snomed_url)
    snomed_data = snomed_response.json()
    parent_concept_id = snomed_data[0]['conceptId']
    parent_term = snomed_data[0]['preferredTerm']

    # Replace code and display
    condition['code']['coding'][0]['code'] = str(parent_concept_id)
    condition['code']['coding'][0]['display'] = parent_term
    condition['code']['text'] = parent_term  # optional but helpful

    # Save to new file
    with open(data_dir / "parent_condition.json", "w") as f:
        json.dump(condition, f, indent=2)

def post_patient(file_name: str, resource_type: str):
    with open(data_dir / f"{file_name}.json") as f:
        resource = json.load(f)
    response = requests.post(
        f"{FHIR_SERVER_URL}/{resource_type}",
        headers={"Content-Type": "application/fhir+json"},
        json=resource
    )
    print(response.status_code)
    patient_response=response.json()
    print(json.dumps(patient_response, indent=2))
    patient_id = patient_response["id"]
    with open(data_dir / "patient_id.txt", "w") as f:
        f.write(patient_id)

def post_condition(file_name: str, resource_type: str):
    with open(data_dir / f"{file_name}.json") as f:
        resource = json.load(f)
    with open(data_dir / "patient_id.txt", "r") as f:
        patient_id = f.read().strip()
    resource["subject"]["reference"] = f"Patient/{patient_id}"
    response = requests.post(
        f"{FHIR_SERVER_URL}/{resource_type}",
        headers={"Content-Type": "application/fhir+json"},
        json=resource
    )
    print(response.status_code)
    print(json.dumps(response.json(), indent=2))
    condition_resource = response.json()
    condition_id = condition_resource["id"]
    with open(data_dir / "condition_id.txt", "w") as f:
        f.write(condition_id)




if __name__ == '__main__':
    print('-------------------------------------------------------------')
    #get_all_resources()
    #get_fhir_patient(resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #search_patient_by_name(name_string='Bailey')
    #search_patient_by_name_gender(name_string= 'Bailey', gender= "female")
    #search_patient_by_bday(bday= '1980-02-21')
    #search_all_condition(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_one_condition(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_concept_id(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_parent(patient_resource_id= '985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #create_patient_json(resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #create_condition_json(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #post_patient("patient", "Patient")
   # post_condition("parent_condition", "Condition")

