# Copyright 2025
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
import re
import shutil
import subprocess
import sys
import time
from typing import Optional

import requests

from config import TestConfig, TestPaths


class DockerHelper:
    """Helper class containing functions to manage Docker Compose operations
    including log capture as well as other actions required to test the
    docker compose setup."""

    def __init__(self, config: TestConfig, paths: TestPaths):
        """Initialize DockerHelper with the Docker Compose directory."""
        self.config = config
        self.paths = paths
        self.started_services = False
        self._create_logs_directory()

    def _create_logs_directory(self):
        """Create the execution_logs directory if it doesn't exist."""
        logs_dir = os.path.join(self.paths.tests_dir, "execution_logs")
        os.makedirs(logs_dir, exist_ok=True)

    def setup_services(self):
        """Start Docker Compose services or verify existing setup based on environment."""
        os.chdir(self.paths.docker_dir)

        if os.getenv("MANAGE_DOCKER") == "true":
            print("Starting Docker Compose services...")
            self._start_docker_services()
            self.started_services = True
        else:
            print("Using existing setup.")
            self._verify_services_running()

    def cleanup_services(self):
        """Capture logs and stop Docker Compose services if we started them."""
        self.capture_container_logs()

        if self.started_services:
            print("Stopping Docker Compose services...")
            self._stop_docker_services()

    def capture_container_logs(self):
        """Capture container logs and save them to execution_logs directory."""
        print("Capturing container logs...")
        logs_dir = os.path.join(self.paths.tests_dir, "execution_logs")
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        try:
            result = subprocess.run(
                ["docker", "compose", "config", "--services"],
                capture_output=True,
                text=True,
                check=True,
            )
            services = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            for service in services:
                if service:
                    try:
                        log_result = subprocess.run(
                            ["docker", "compose", "logs", "--no-color", service],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        log_file = os.path.join(logs_dir, f"{service}_{timestamp}.log")
                        with open(log_file, "w") as f:
                            f.write(f"=== Logs for service: {service} ===\n")
                            f.write(
                                f"=== Captured at: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
                            )
                            f.write(log_result.stdout)
                        print(f"Saved logs for {service} to {log_file}")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to capture logs for service {service}: {e}")

            try:
                combined_result = subprocess.run(
                    ["docker", "compose", "logs", "--no-color"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                combined_log_file = os.path.join(logs_dir, f"combined_{timestamp}.log")
                with open(combined_log_file, "w") as f:
                    f.write("=== Combined Docker Compose Logs ===\n")
                    f.write(
                        f"=== Captured at: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
                    )
                    f.write(combined_result.stdout)
                print(f"Saved combined logs to {combined_log_file}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to capture combined logs: {e}")

        except subprocess.CalledProcessError as e:
            print(f"Failed to get service list: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")

    def _start_docker_services(self):
        """Start Docker Compose services."""
        try:
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                capture_output=True,
                text=True,
                check=True,
            )
            print("Docker Compose started successfully")
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Failed to start Docker Compose: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            sys.exit(1)

    def _stop_docker_services(self):
        """Stop Docker Compose services."""
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
        """Verify that required Docker Compose services are running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                check=True,
            )
            running_services = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            if not running_services:
                print("Warning: No running Docker Compose services found")
            else:
                print(f"Found running services: {', '.join(running_services)}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to verify services: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")


class ClickHouseHelper:
    """Helper class for ClickHouse database operations."""

    def __init__(self, config: TestConfig, paths: TestPaths):
        """Initialize ClickHouseHelper with test configuration."""
        self.config = config
        self.paths = paths

    def query(self, test_case, sql: str = "SELECT 1") -> dict:
        """Execute a ClickHouse query and return first row as dictionary."""
        client = self._create_client()
        try:
            result = client.execute(sql, with_column_types=True)

            if not result:
                return {}
            print(f"Query executed successfully: {sql[:50]}...")

            data, column_info = result
            column_names = [col[0] for col in column_info]

            if data:
                return dict(zip(column_names, data[0]))
            return {}

        except Exception as e:
            test_case.fail(f"ClickHouse query failed. SQL: '{sql}', Error: {e}")
        finally:
            client.disconnect()

    def ddl(self, test_case, sql: str) -> bool:
        """Execute a ClickHouse DDL command."""
        client = self._create_client()
        try:
            client.execute(sql)
            print(f"DDL executed successfully: {sql[:50]}...")
            return True

        except Exception as e:
            test_case.fail(f"ClickHouse DDL failed. SQL: '{sql}', Error: {e}")
        finally:
            client.disconnect()

    def create_iceberg_rest_catalog(
        self, test_case, name, drop_first: bool = False
    ) -> bool:
        """Create an Iceberg catalog in ClickHouse using profile configuration for settings."""
        if drop_first:
            self.ddl(test_case, f"DROP DATABASE IF EXISTS {name}")

        # Create database, omitting unset settings.
        ice_setting_auth_header = (
            f", auth_header = '{self.config.ice_setting_auth_header}'"
        )
        ice_setting_warehouse = f", warehouse = '{self.config.ice_setting_warehouse}'"
        if self.config.ice_setting_storage_endpoint:
            ice_setting_storage_endpoint = f", storage_endpoint = '{self.config.ice_setting_storage_endpoint}'"
        else:
            ice_setting_storage_endpoint = ""
        if self.config.ice_setting_warehouse:
            ice_setting_warehouse = f", warehouse = '{self.config.ice_setting_warehouse}'"
        else:
            ice_setting_warehouse = ""
        create_ddl = f"""
        CREATE DATABASE ice_test ENGINE = DataLakeCatalog('http://ice-rest-catalog:5000')
        SETTINGS
          catalog_type = 'rest'
          {ice_setting_auth_header} {ice_setting_warehouse} {ice_setting_storage_endpoint}
        """

        return self.ddl(test_case, create_ddl)

    def _create_client(self):
        """Create a ClickHouse client connection."""
        from clickhouse_driver import Client

        return Client(
            host=self.config.ch_host,
            port=self.config.ch_port,
            user=self.config.ch_user,
            password=self.config.ch_password,
        )


class OsHelper:
    """Helper class for OS-level operations including command execution,
    executable checks, and HTTP requests."""

    def __init__(self, config: TestConfig, paths: TestPaths):
        """Initialize OsHelper with test configuration and paths."""
        self.config = config
        self.paths = paths

    def run_ice_command(
        self,
        test_case,
        ice_command: list,
        expected_output: Optional[str] = None,
        expected_pattern: Optional[str] = None,
        expected_returncode: int = 0,
        ignore_returncode: bool = False,
    ):
        """Run an Ice client command and verify expected output."""
        # Ensure ice is available.
        self.check_executable_in_path(test_case, "ice")

        # Prefix ice command and config file, then execute command.
        ice_cfg_file = os.path.join(self.paths.tests_dir, self.config.ice_config)
        ice_command = ["ice", "-c", ice_cfg_file] + ice_command
        self.run_command(
            test_case,
            ice_command,
            expected_output,
            expected_pattern,
            expected_returncode,
            ignore_returncode,
        )

    def run_command(
        self,
        test_case,
        command: list,
        expected_output: Optional[str] = None,
        expected_pattern: Optional[str] = None,
        expected_returncode: int = 0,
        ignore_returncode: bool = False,
    ):
        """Run a command and verify expected output."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if not ignore_returncode and result.returncode != expected_returncode:
                test_case.fail(
                    f"Command {command} returned {result.returncode}, "
                    f"expected {expected_returncode}\n"
                    f"stdout: {result.stdout}\nstderr: {result.stderr}"
                )

            combined_output = result.stdout + result.stderr

            if expected_output is not None and expected_output not in combined_output:
                test_case.fail(
                    f"Expected output '{expected_output}' not found in command output\n"
                    f"stdout: {result.stdout}\nstderr: {result.stderr}"
                )

            if expected_pattern is not None:
                if not re.search(expected_pattern, combined_output):
                    test_case.fail(
                        f"Expected pattern '{expected_pattern}' not found in output\n"
                        f"stdout: {result.stdout}\nstderr: {result.stderr}"
                    )

            print(f"Command executed successfully: {' '.join(command[:3])}...")
            return result

        except Exception as e:
            test_case.fail(f"Failed to run command {command}: {e}")

    def run_python_script(self, test_case, script_name: str):
        """Run a Python script from the python directory."""
        try:
            script_path = os.path.join(self.paths.python_dir, script_name)

            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.paths.python_dir,
            )
            print(f"{script_name} executed successfully")
            print(f"stdout: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            test_case.fail(
                f"{script_name} failed with exit code {e.returncode}\n"
                f"stdout: {e.stdout}\nstderr: {e.stderr}"
            )
        except FileNotFoundError:
            test_case.fail(f"{script_name} not found in {self.paths.python_dir}")

    def check_executable_in_path(self, test_case, executable_name: str) -> str:
        """Verify an executable exists in PATH."""
        path = shutil.which(executable_name)
        if path is None:
            test_case.fail(f"Executable '{executable_name}' not found in PATH")
        print(f"Found '{executable_name}' at: {path}")
        return path

    def check_executable_version(
        self,
        test_case,
        executable_name: str,
        min_version: str = "1.0.0",
        version_flag: str = "--version",
        version_pattern: Optional[str] = None,
    ) -> tuple:
        """Verify an executable meets minimum version requirements."""
        try:
            result = subprocess.run(
                [executable_name, version_flag],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout + result.stderr

            if version_pattern:
                match = re.search(version_pattern, output)
                version_str = match.group(1) if match else None
            else:
                version_str = output

            actual_version = self._parse_version(version_str) if version_str else None
            min_version_tuple = self._parse_version(min_version)

            if actual_version is None:
                test_case.fail(
                    f"Could not parse version from '{executable_name} {version_flag}'\n"
                    f"Output: {output}"
                )

            if actual_version < min_version_tuple:
                test_case.fail(
                    f"'{executable_name}' version {'.'.join(map(str, actual_version))} "
                    f"is less than required {min_version}"
                )

            version_display = ".".join(map(str, actual_version))
            print(f"'{executable_name}' version {version_display} >= {min_version}")
            return actual_version

        except FileNotFoundError:
            test_case.fail(f"Executable '{executable_name}' not found")
        except Exception as e:
            test_case.fail(f"Failed to check version of '{executable_name}': {e}")

    def http_get(
        self,
        test_case,
        url: str,
        timeout: int = 10,
        expected_status_code: int = 200,
        auth_header: Optional[str] = None,
    ):
        """Perform an HTTP GET request with error handling."""
        try:
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            response = requests.get(url, timeout=timeout, headers=headers)
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

    def generate_basic_auth_header(self, username: str, password: str) -> str:
        """Generate a properly encoded basic authentication header."""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    def _parse_version(self, version_string: str) -> Optional[tuple]:
        """Parse a version string into a tuple of integers for comparison."""
        match = re.search(r"(\d+)\.(\d+)\.?(\d*)", version_string)
        if not match:
            return None
        major, minor = int(match.group(1)), int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0
        return (major, minor, patch)
