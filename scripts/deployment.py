import os
import subprocess
import platform
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the AWS region, profile, and ECR repo details
AWS_REGION = "us-west-2"
AWS_PROFILE = "curlytales_deployment"
ECR_REPO = "201733751407.dkr.ecr.us-west-2.amazonaws.com"
IMAGE_NAME = "ct-genai-lambda"
DOCKERFILE = "Lambda.Dockerfile"
REPO_NAME = "ct-genai/backend-api"  # ECR Repository Name (with optional path)

# Define the Lambda function name
LAMBDA_FUNCTION_NAME = "ct-genai-backend"

# Load AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')  # Optional, if using temporary credentials

def run_command(command):
    """Run a shell command and handle errors."""
    print(f"Executing: {command}")
    try:
        subprocess.run(command, shell=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        sys.exit(1)

def aws_profile_exists(profile):
    """Check if the AWS CLI profile already exists."""
    try:
        subprocess.run(
            f"aws configure list --profile {profile}",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def configure_aws_profile():
    """Configure AWS CLI profile using environment variables if not already configured."""
    print("Checking if AWS CLI profile exists...")
    if aws_profile_exists(AWS_PROFILE):
        print(f"AWS CLI profile '{AWS_PROFILE}' already exists. Skipping configuration.")
    else:
        print(f"AWS CLI profile '{AWS_PROFILE}' does not exist. Configuring profile...")
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("Error: AWS credentials not found in environment variables!")
            sys.exit(1)

        configure_commands = [
            f"aws configure set aws_access_key_id {AWS_ACCESS_KEY_ID} --profile {AWS_PROFILE}",
            f"aws configure set aws_secret_access_key {AWS_SECRET_ACCESS_KEY} --profile {AWS_PROFILE}",
            f"aws configure set region {AWS_REGION} --profile {AWS_PROFILE}"
        ]

        # If using temporary credentials, set the session token
        if AWS_SESSION_TOKEN:
            configure_commands.append(f"aws configure set aws_session_token {AWS_SESSION_TOKEN} --profile {AWS_PROFILE}")

        for command in configure_commands:
            run_command(command)
        print(f"AWS CLI profile '{AWS_PROFILE}' configured successfully.")

def docker_login():
    """Log into AWS ECR."""
    print("Logging into AWS ECR...")
    login_command = (
        f"aws ecr get-login-password --region {AWS_REGION} --profile {AWS_PROFILE} | "
        f"docker login --username AWS --password-stdin {ECR_REPO}"
    )
    run_command(login_command)
    print("Docker login successful.")

def build_image():
    """Build the Docker image."""
    print(f"Building Docker image '{IMAGE_NAME}' using '{DOCKERFILE}'...")
    build_command = f"docker build -t {IMAGE_NAME} -f {DOCKERFILE} ."
    run_command(build_command)
    print(f"Docker image '{IMAGE_NAME}' built successfully.")

def tag_image():
    """Tag the Docker image for ECR."""
    print(f"Tagging Docker image '{IMAGE_NAME}:latest' for ECR repository '{REPO_NAME}'...")
    tag_command = f"docker tag {IMAGE_NAME}:latest {ECR_REPO}/{REPO_NAME}:latest"
    run_command(tag_command)
    print(f"Docker image tagged as '{ECR_REPO}/{REPO_NAME}:latest'.")

def push_image():
    """Push the Docker image to AWS ECR."""
    print(f"Pushing Docker image '{ECR_REPO}/{REPO_NAME}:latest' to AWS ECR...")
    push_command = f"docker push {ECR_REPO}/{REPO_NAME}:latest"
    run_command(push_command)
    print(f"Docker image '{REPO_NAME}:latest' pushed to AWS ECR successfully.")

def deploy_lambda():
    """
    Deploy the newly pushed Docker image to the specified AWS Lambda function.

    This function updates the Lambda function's code to use the latest Docker image from ECR.
    """
    print(f"Deploying new image to Lambda function '{LAMBDA_FUNCTION_NAME}'...")

    # Construct the full image URI
    image_uri = f"{ECR_REPO}/{REPO_NAME}:latest"
    print(f"Image URI to deploy: {image_uri}")

    # AWS CLI command to update Lambda function code
    update_command = (
        f"aws lambda update-function-code "
        f"--function-name {LAMBDA_FUNCTION_NAME} "
        f"--image-uri {image_uri} "
        f"--profile {AWS_PROFILE} "
        f"--region {AWS_REGION}"
    )

    # Execute the update command
    run_command(update_command)
    print(f"Lambda function '{LAMBDA_FUNCTION_NAME}' updated successfully with image '{image_uri}'.")

def main():
    try:
        # Ensure AWS credentials are loaded from the environment
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in the environment variables or .env file.")
            sys.exit(1)

        # Detect platform (Windows or Linux/macOS)
        current_os = platform.system().lower()
        if current_os == "windows":
            print("Running on Windows...")
        else:
            print("Running on Linux/macOS...")

        # Step 1: Configure AWS CLI profile
        configure_aws_profile()

        # Step 2: Log into ECR
        docker_login()

        # Step 3: Build Docker image
        build_image()

        # Step 4: Tag Docker image
        tag_image()

        # Step 5: Push Docker image
        push_image()

        # Step 6: Deploy the new image to Lambda
        deploy_lambda()

        print("Deployment to AWS ECR and Lambda completed successfully!")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
