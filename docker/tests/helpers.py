# Copyright 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import os
import subprocess
import sys
import time

import requests


class DockerHelper:
    """Helper class containing functions to manage Docker Compose operations
       including log capture as well as other actions require to test the
       docker compose setup"""

    def __init__(self, docker_dir):
        """Initialize DockerHelper with the Docker Compose directory"""
        self.docker_dir = docker_dir
        self.started_services = False
        self._create_logs_directory()

    def _create_logs_directory(self):
        """Create the test_logs directory if it doesn't exist"""
        logs_dir = os.path.join(self.docker_dir, "test_logs")
        os.makedirs(logs_dir, exist_ok=True)

    def setup_services(self):
        """Start Docker Compose services or verify existing setup based on environment"""
        os.chdir(self.docker_dir)

        if os.getenv('SKIP_DOCKER_SETUP') == 'true':
            print("Using existing Docker Compose setup...")
            self._verify_services_running()
        else:
            print("Starting Docker Compose services...")
            self._start_docker_services()
            self.started_services = True

    def cleanup_services(self):
        """Capture logs and stop Docker Compose services if we started them"""
        # Always capture logs for debugging
        self.capture_container_logs()

        # Only stop services if we started them
        if self.started_services:
            print("Stopping Docker Compose services...")
            self._stop_docker_services()

    def _start_docker_services(self):
        """Start Docker Compose services"""
        try:
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                capture_output=True,
                text=True,
                check=True,
            )
            print("Docker Compose started successfully")

            # Wait a bit for services to be ready
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Failed to start Docker Compose: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            sys.exit(1)

    def _stop_docker_services(self):
        """Stop Docker Compose services"""
        try:
            subprocess.run(
                ["docker", "compose", "down"],
                capture_output=True,
                text=True,
                check=True,
            )
            print("Docker Compose stopped successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to stop Docker Compose: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")

    def _verify_services_running(self):
        """Verify that required Docker Compose services are running"""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                check=True,
            )
            running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
            if not running_services:
                print("Warning: No running Docker Compose services found")
            else:
                print(f"Found running services: {', '.join(running_services)}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to verify services: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")

    def capture_container_logs(self):
        """Capture container logs and save them to test_logs directory"""
        print("Capturing container logs...")
        logs_dir = os.path.join(self.docker_dir, "test_logs")
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        try:
            # Get list of services
            result = subprocess.run(
                ["docker", "compose", "config", "--services"],
                capture_output=True,
                text=True,
                check=True,
            )
            services = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # Capture logs for each service
            for service in services:
                if service:  # Skip empty lines
                    try:
                        log_result = subprocess.run(
                            ["docker", "compose", "logs", "--no-color", service],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        log_file = os.path.join(logs_dir, f"{service}_{timestamp}.log")
                        with open(log_file, 'w') as f:
                            f.write(f"=== Logs for service: {service} ===\n")
                            f.write(f"=== Captured at: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                            f.write(log_result.stdout)
                        print(f"Saved logs for {service} to {log_file}")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to capture logs for service {service}: {e}")

            # Also capture combined logs
            try:
                combined_result = subprocess.run(
                    ["docker", "compose", "logs", "--no-color"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                combined_log_file = os.path.join(logs_dir, f"combined_{timestamp}.log")
                with open(combined_log_file, 'w') as f:
                    f.write(f"=== Combined Docker Compose Logs ===\n")
                    f.write(f"=== Captured at: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                    f.write(combined_result.stdout)
                print(f"Saved combined logs to {combined_log_file}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to capture combined logs: {e}")

        except subprocess.CalledProcessError as e:
            print(f"Failed to get service list: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")


def generate_basic_auth_header(username, password):
    """Generate a properly encoded basic authentication header"""
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
        "utf-8"
    )
    return f"Basic {encoded_credentials}"


def http_get_helper(test_case, url, timeout=10, expected_status_code=200, auth_header=None):
    """Helper function to perform HTTP GET request with error handling"""
    try:
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header

        response = requests.get(url, timeout=timeout, headers=headers)
        # Check if status code matches expected.
        if response.status_code == expected_status_code:
            print(f"HTTP GET to {url} successful: {response.status_code}")
            return response
        else:
            test_case.fail(
                f"Expected status {expected_status_code}, got {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed for URL: {url}")
        print(f"Exception: {e}")
        test_case.fail(f"HTTP request failed: {e}")


def run_python_script_helper(test_case, script_name):
    """Helper function to run a Python script from the parent directory"""
    try:
        # Get the parent directory (docker) where the Python scripts should be
        test_dir = os.path.dirname(os.path.abspath(__file__))
        docker_dir = os.path.dirname(test_dir)
        script_path = os.path.join(docker_dir, script_name)

        # Run the script and check for success
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True,
            cwd=docker_dir
        )
        print(f"{script_name} executed successfully")
        print(f"stdout: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        test_case.fail(f"{script_name} failed with exit code {e.returncode}\n"
            f"stdout: {e.stdout}\nstderr: {e.stderr}")
    except FileNotFoundError:
        test_case.fail(f"{script_name} not found in parent directory")
