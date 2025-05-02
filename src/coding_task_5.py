import json
import requests
from pathlib import Path
from hl7apy.core import Message
from datetime import datetime

BASE_HERMES_URL = "http://159.65.173.51:8080/v1/snomed/concepts"
data_dir = Path("data")

def create_adt_message():

    with open(data_dir / "patient.json") as f:
        patient_data = json.load(f)

    with open(data_dir / "condition.json") as f:
        condition_data = json.load(f)

    # Extract patient details
    patient_id = patient_data["id"]
    name = patient_data["name"][0]
    full_name = f"{name.get('family', '')}^{name.get('given', [''])[0]}"
    gender = patient_data.get("gender", "").upper()[0]
    birthdate = patient_data.get("birthDate", "").replace("-", "")
    address = patient_data["address"][0]["line"][0]
    city = patient_data["address"][0]["city"]
    state = patient_data["address"][0]["state"]
    zip_code = patient_data["address"][0]["postalCode"]

    now = datetime.now().strftime("%Y%m%d%H%M%S")

    # Extract SNOMED condition
    condition_code = condition_data["code"]["coding"][0]["code"]
    condition_display = condition_data["code"]["coding"][0]["display"]

    # Fetch ICD-10 mapping
    map_url = f"{BASE_HERMES_URL}/{condition_code}/map/447562003"
    map_response = requests.get(map_url)
    mapping_data = map_response.json()
    if not mapping_data:
        print(f"No ICD-10 mapping found for SNOMED code {condition_code}")
        raise ValueError(f"No ICD-10 mapping found for SNOMED code {condition_code}")

    mapping = mapping_data[0]
    icd_code = mapping["mapTarget"]
    icd_display = mapping.get("mapTargetName", "ICD-10 Term")

    print(f"{icd_code} is the mapped ICD code for SNOMED code: {condition_code} - {condition_display}")

    msg = Message("ADT_A01")

    msg.msh.msh_3 = "MyApp"
    msg.msh.msh_4 = "SendingFacility"
    msg.msh.msh_5 = "ReceivingApp"
    msg.msh.msh_6 = "ReceivingFacility"
    msg.msh.msh_7 = "20250430120000"
    msg.msh.msh_9 = "ADT^A01"
    msg.msh.msh_10 = "MSG00001"
    msg.msh.msh_11 = "P"
    msg.msh.msh_12 = "2.5"

    msg.pid.pid_1 = "1"
    msg.pid.pid_3 = patient_id
    msg.pid.pid_5 = full_name
    msg.pid.pid_7 = birthdate
    msg.pid.pid_8 = gender
    msg.pid.pid_11 = f"{address}^{city}^{state}^{zip_code}^^H"

    msg.pv1.pv1_1 = "1"
    msg.pv1.pv1_2 = "I"

    if icd_code:
        msg.dg1.dg1_1 = "1"
        msg.dg1.dg1_3 = f"{icd_code}^{icd_display}^I10"
        msg.dg1.dg1_4 = condition_display

    # Save message
    with open(data_dir / "hl7_message.txt", "w") as f:
        f.write(msg.to_er7())
    print("hl7 message created")

create_adt_message()
