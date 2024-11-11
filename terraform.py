import requests
import time

class TerraformCloudAPI:
    def __init__(self, token, organization):
        self.token = token
        self.organization = organization
        self.api_url = "https://app.terraform.io/api/v2"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }

    def get_workspace_id(self, workspace_name):
        """Get workspace ID from workspace name"""
        url = f"{self.api_url}/organizations/{self.organization}/workspaces/{workspace_name}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["data"]["id"]

    def create_run(self, workspace_id, message="API triggered run"):
        """Create a new run in the workspace"""
        url = f"{self.api_url}/runs"
        payload = {
            "data": {
                "attributes": {
                    "message": message,
                    "auto-apply": True  # Set to False if you want manual applies
                },
                "type": "runs",
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id
                        }
                    }
                }
            }
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()["data"]["id"]

    def get_run_status(self, run_id):
        """Get the current status of a run"""
        url = f"{self.api_url}/runs/{run_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["data"]["attributes"]["status"]

    def wait_for_run(self, run_id, timeout=300):
        """Wait for a run to complete, with timeout in seconds"""
        start_time = time.time()
        while True:
            status = self.get_run_status(run_id)
            
            if status in ["applied", "planned_and_finished", "completed"]:
                return True, status
            elif status in ["errored", "canceled", "discarded"]:
                return False, status
            
            if time.time() - start_time > timeout:
                return False, "timeout"
            
            time.sleep(10)

    def create_destroy_run(self, workspace_id, message="API triggered destroy"):
        """Create a destroy plan run"""
        url = f"{self.api_url}/runs"
        payload = {
            "data": {
                "attributes": {
                    "message": message,
                    "auto-apply": True,
                    "is-destroy": True
                },
                "type": "runs",
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id
                        }
                    }
                }
            }
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()["data"]["id"]
