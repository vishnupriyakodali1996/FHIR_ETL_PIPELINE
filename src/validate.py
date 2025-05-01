import requests
import json
from pathlib import Path

data_dir = Path.cwd() / "data"
FHIR_SERVER_URL = "http://137.184.71.65:8080/fhir"


def validate_resource(file_name: str, resource_type: str):
    with open(data_dir / f"{file_name}.json") as f:
        resource = json.load(f)
    response = requests.post(
        f"{FHIR_SERVER_URL}/{resource_type}/$validate",
        headers={"Content-Type": "application/fhir+json"},
        json=resource
    )
    print(response.status_code)
    print(json.dumps(response.json(), indent=2))



if __name__ == '__main__':
    #validate_resource("patient", "Patient")
    #validate_resource("parent_condition", "Condition")
    validate_resource(file_name= "child_condition", resource_type= "Condition")


