import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"


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


#Demonstrate using FHIR search parameters (e.g., name, birth date, gender, condition, _lastUpdated, etc.) to retrieve patient data from the OpenEMR FHIR server.
def search_patient_by_name(name_string):
    url = f'{BASE_URL}/Patient?name={name_string}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())
    print('------------------------------------------------------------- 3')


#Search for all the conditions of this patient.
def search_all_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    pprint(data)
    print(f"Total num of conditions for patient: {len(data['entry'])}")
    num = 0
    for items in data['entry']:
        for dicts in items.get('resource')['code']['coding']:
            code = dicts.get('code')
            condition = dicts.get('display')
            num = num + 1
            print(f"Condition ({num}) - code: {code} - condition: {condition}")
    print('------------------------------------------------------------- 3')

#get any one condition of this patient
def search_one_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    for items in data['entry']:
        for dicts in items.get('resource')['code']['coding']:
            code = dicts.get('code')
            condition = dicts.get('display')
            print(f"First condition of patient - code: {code} - condition: {condition}")
        break
    print('------------------------------------------------------------- 3')


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
        print('------------------------------------------------------------- 5')

def search_patient_by_bday(bday):
    url = f'{BASE_URL}/Patient?birthdate={bday}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())
    print('------------------------------------------------------------- 6')

def get_concept_id(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    first_entry = data['entry'][0]
    resource = first_entry.get('resource')
    code_section = resource.get('code')
    codings = code_section.get('coding')
    for coding in codings:
        code = coding.get('code')
        display = coding.get('display')
        print(f"Concept ID: {code}, Condition: {display}")
    print('------------------------------------------------------------- 3')

if __name__ == '__main__':
    print('-------------------------------------------------------------')
    #get_all_resources()
    #get_fhir_patient(resource_id='985ac6ea-c3e8-4bd4-ae43-41683cb26135')
    search_all_condition(patient_resource_id='985ac6ea-c3e8-4bd4-ae43-41683cb26135')
    #search_patient_by_name(name_string='Kuvalis')
    #search_patient_by_bday(bday= '1995-04-23')
    #search_one_condition(patient_resource_id='985ac6ea-c3e8-4bd4-ae43-41683cb26135')
    #snomed_concept_id = "80967001"
    get_concept_id(patient_resource_id='985ac6ea-c3e8-4bd4-ae43-41683cb26135')