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
BASE_HERMES_URL = 'http://159.65.173.51:8080/v1/snomed'
primary_care_EHR = "http://137.184.71.65:8080/fhir"
FHIR_SERVER_URL = "http://137.184.71.65:8080/fhir"

# Get patient
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
    pprint(nice_entry)
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
    #print(response.url)
    data = response.json()
    first_entry = data['entry'][16]
    resource = first_entry.get('resource')
    code_section = resource.get('code')
    codings = code_section.get('coding')
    for coding in codings:
        code = coding.get('code')
        display = coding.get('display')
        print(f"{code} is the concept ID for Condition: {display}")


# Get child term for the condition of the patient
def get_child(patient_resource_id):
    # Fetch condition from FHIR server
    condition_url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=condition_url, headers=get_headers())
    print(response.url)
    #pprint(response.json())
    #pprint(response.json()['entry'][16])
    entry = response.json()['entry'][16]['resource']
    # Extract SNOMED code
    code = entry['code']['coding'][0]['code']
    display = entry['code']['coding'][0]['display']

    # Fetch SNOMED child
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=<{code}'
    snomed_response = requests.get(snomed_url)
    #print(snomed_response.url)
    #pprint(snomed_response.json())
    data= snomed_response.json()
    #pprint(data)
    ch_concept_id= data[1]["conceptId"]
    ch_pref_term= data[1]["preferredTerm"]
    # get the finding site for child
    snomed_url = (f'{BASE_HERMES_URL}/concepts/{code}/properties?expand=0&format=id:syn')
    snomed_resp = requests.get(snomed_url)
    finding_site_data = snomed_resp.json()
    pprint(finding_site_data)
    finding_site = finding_site_data['1'].get('363698007:Finding site')
    #print(f"Finding site:{finding_site}")
    find_site_code = finding_site.split(":")[0]
    find_site_name = finding_site.split(":")[1]
    #print(f"Finding site for {code} is {find_site_name}")
    print(f"Child SNOMED condition for {display} is {ch_pref_term} and concept-ID is {ch_concept_id}")
    print("-------------------------------------------------------------------------------------")

# Creating child condition to JSON file
str_def_url_condition= "http://hl7.org/fhir/StructureDefinition/Condition"
def create_child_condition_json(patient_resource_id):
    # Get original condition
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    condition = data['entry'][16]['resource']
    condition["meta"]["profile"] = [str_def_url_condition]
    # Extract original SNOMED code
    original_code = condition['code']['coding'][0]['code']

    # Fetch SNOMED child condition
    snomed_url = f'{BASE_HERMES_URL}/search?constraint=<{original_code}'
    snomed_response = requests.get(snomed_url)
    #print(snomed_response.url)
    #pprint(snomed_response.json())
    data = snomed_response.json()
    ch_concept_id = data[1]["conceptId"]
    ch_pref_term = data[1]["preferredTerm"]

    # Getting body site for child condition from SNOMED
    snomed_url = (f'{BASE_HERMES_URL}/concepts/{ch_concept_id}/properties?expand=0&format=id:syn')
    snomed_resp = requests.get(snomed_url)
    finding_site_data = snomed_resp.json()
    finding_site = finding_site_data['1'].get('363698007:Finding site')
    find_site_code = finding_site.split(":")[0]
    find_site_name = finding_site.split(":")[1]

    # Replace patient status the condition code and display
    condition['code']['coding'][0]['code'] = str(ch_concept_id)
    condition['code']['coding'][0]['display'] = ch_pref_term
    condition['code']['text'] = ch_pref_term  # optional but helpful
    for item in condition["clinicalStatus"]["coding"]:
        item["code"] = "active"
        item["display"] = "Active"

    # Creating a body site
    condition["bodySite"] = [{
        "coding": [{
            "system": "http://snomed.info/sct",
            "code": find_site_code,
            "display": find_site_name
        }],
        "text": find_site_name
    }]
# Save to new file
    with open(data_dir / "child_condition.json", "w") as f:
        json.dump(condition, f, indent=2)

# Posting the condition to primary care EMR
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
    with open(data_dir / "child_condition_id.txt", "w") as f:
        f.write(condition_id)

if __name__ == '__main__':
    print('-------------------------------------------------------------')
    #get_fhir_patient(resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_one_condition(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #get_child(patient_resource_id= '985ac812-ddd2-49ce-9806-160e27d7cfa7')
    #create_child_condition_json(patient_resource_id='985ac812-ddd2-49ce-9806-160e27d7cfa7')
    post_condition("child_condition", "Condition")
