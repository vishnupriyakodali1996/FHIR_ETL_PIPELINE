import json
import requests
import datetime
from pprint import pprint
from pathlib import Path
from src.registration import data_dir
import matplotlib.pyplot as plt

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
BASE_HERMES_URL = 'http://159.65.173.51:8080/v1/snomed'
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


# To know all the resources in FHIR data
def get_all_resources():
    url = f"{BASE_URL}/metadata"
    response = requests.get(url=url, headers=get_headers())
    data = response.json()
    for rest in data["rest"]:
        for resource in rest["resource"]:
            print(resource["type"])


def get_patient_ids():
    url = f"{BASE_URL}/Patient"
    response = requests.get(url, headers=get_headers())
    data = response.json()
    return [entry["resource"]["id"] for entry in data.get("entry", [])]

def count_bp_observations(patient_ids):
    bp_count = 0
    for pid in patient_ids:
        obs_url = f"{BASE_URL}/Observation?patient={pid}&code=http://loinc.org|85354-9"
        response = requests.get(obs_url, headers=get_headers())
        data = response.json()
        if "entry" in data:
            bp_count += 1
    return bp_count

def visualize():
    patient_ids = get_patient_ids()
    total = len(patient_ids)
    with_bp = count_bp_observations(patient_ids)

    categories = ["Total Patients", "With BP Observation"]
    values = [total, with_bp]
    colors = ["#A3D5FF", "#7BD389"]  # soft blue, soft green

    bars = plt.bar(categories, values, color=colors)
    plt.title("Disparity in Blood Pressure Observation", fontsize=14)
    plt.ylabel("Number of Patients")

    # Add number labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + 0.5, str(height), ha='center', va='bottom', fontsize=12)

    plt.ylim(0, total + 5)
    plt.tight_layout()
    plt.show()

visualize()
