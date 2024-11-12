import requests
import time
from requests.auth import HTTPBasicAuth

class AWXClient:
    def __init__(self, awx_url, awx_token):
        self.awx_url = awx_url.rstrip('/')
        print(f"AWX URL: {self.awx_url}")
        print(f"AWX Token: {awx_token}")
        self.basic = HTTPBasicAuth('peet', awx_token)
        self.headers = {
            # "Authorization": f"Bearer {awx_token}",
            "Content-Type": "application/json"
        }

    def launch_job_template(self, template_id, extra_vars=None):
        """Launch an AWX job template and return the job ID"""
        url = f"{self.awx_url}/api/v2/job_templates/{template_id}/launch/"
        payload = {"extra_vars": extra_vars} if extra_vars else {}
        
        response = requests.post(url, headers=self.headers, json=payload,auth=self.basic)
        response.raise_for_status()
        return response.json()["id"]

    def get_job_status(self, job_id):
        """Get the current status of a job"""
        url = f"{self.awx_url}/api/v2/workflow_jobs/{job_id}/"
        response = requests.get(url, headers=self.headers,auth=self.basic)
        response.raise_for_status()
        return response.json()

    def wait_for_job(self, job_id, timeout=1800, interval=10):
        """Wait for a job to complete and return the final status"""
        start_time = time.time()
        while True:
            job_info = self.get_job_status(job_id)
            status = job_info["status"]
            
            if status in ["successful", "failed", "error", "canceled"]:
                return job_info
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
            
            time.sleep(interval)

    def print_job_summary(self, job_info):
        """Print a summary of the job results"""
        print("\nAWX Job Summary:")
        print(f"Job ID: {job_info['id']}")
        print(f"Name: {job_info['name']}")
        print(f"Status: {job_info['status']}")
        print(f"Started: {job_info['started']}")
        print(f"Finished: {job_info['finished']}")
        print(f"Elapsed: {job_info['elapsed']} seconds")
        
        if job_info['status'] == 'failed':
            print(f"Failed hosts: {job_info.get('failed_hosts', 'N/A')}")
