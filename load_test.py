#!/usr/bin/python
import argparse
import os
import requests
import json

from terraform import TerraformCloudAPI
from awx import AWXClient

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Terraform Cloud Workspace Manager')
    parser.add_argument('--destroy', action='store_true', 
                      help='Destroy all resources in the workspace')
    args = parser.parse_args()

    # Get these from environment variables for security
    token = os.getenv("TF_API_TOKEN")
    organization = "dcs-tf-org"
    workspace_name = "iac-ansible-load-testing-WL"
    awx_url = os.getenv("AWX_URL")
    awx_token = os.getenv("AWX_TOKEN")
    awx_template_id = 9

    if not all([token, organization, workspace_name,awx_url,awx_token]):
        raise ValueError("Missing required environment variables")

    # Initialize the API client
    tf_client = TerraformCloudAPI(token, organization)
    awx_client = AWXClient(awx_url, awx_token)

    try:
        # Get workspace ID
        workspace_id = tf_client.get_workspace_id(workspace_name)
        print(f"Found workspace ID: {workspace_id}")

        if args.destroy:
            print("Destroy flag detected - initiating destroy operation...")
            
            # Create a destroy run
            destroy_run_id = tf_client.create_destroy_run(workspace_id)
            print(f"Created destroy run ID: {destroy_run_id}")

            # Wait for the destroy to complete
            success, final_status = tf_client.wait_for_run(destroy_run_id, timeout=800)
            print(f"Destroy run completed with status: {final_status}")

            if not success:
                raise Exception(f"Destroy run failed with status: {final_status}")
            
            print("Resources destroyed successfully")

        else:
            # Create a normal run
            run_id = tf_client.create_run(workspace_id)
            print(f"Created run ID: {run_id}")

            # Wait for the run to complete
            success, final_status = tf_client.wait_for_run(run_id,timeout=800)
            print(f"Run completed with status: {final_status}")
            if success:
                print("\nLaunching AWX job template...")
                # extra_vars = json.loads(args.awx_extra_vars) if args.awx_extra_vars else None
                extra_vars = None
                job_id = awx_client.launch_job_template(awx_template_id, extra_vars)
                print(f"AWX Job launched with ID: {job_id}")

                # Wait for AWX job to complete
                try:
                    job_info = awx_client.wait_for_job(job_id)
                    awx_client.print_job_summary(job_info)
                    
                    if job_info["status"] != "successful":
                        raise Exception(f"AWX job failed with status: {job_info['status']}")
                except Exception as e:
                    print(f"AWX job error: {e}")
                    raise            

            if not success:
                raise Exception(f"Run failed with status: {final_status}")
            print("Destroy any resources created by the run...")
            destroy_run_id = tf_client.create_destroy_run(workspace_id)

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()