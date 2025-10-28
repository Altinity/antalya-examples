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

import os
import unittest
from urllib.parse import quote

from helpers import DockerHelper, generate_basic_auth_header, http_get_helper, run_python_script_helper


class DockerTestFramework(unittest.TestCase):
    """Docker test framework that manages Docker Compose services and captures logs"""
    _docker_helper = None

    @classmethod
    def setUpClass(cls):
        """Start Docker Compose services before running tests or verify existing setup"""
        # Set up directory paths
        test_dir = os.path.dirname(os.path.abspath(__file__))
 
        # Initialize Docker helper and setup services
        cls._docker_helper = DockerHelper(test_dir)
        cls._docker_helper.setup_services()

    @classmethod
    def tearDownClass(cls):
        """Capture logs and stop Docker Compose services if we started them"""
        if cls._docker_helper:
            cls._docker_helper.cleanup_services()

    def test_ice_catalog_liveness(self):
        """Confirm ice catalog on 5000 can list namespaces"""
        http_get_helper(self, "http://localhost:5000/v1/namespaces", auth_header="Bearer foo")

    def test_vector_server_liveness(self):
        """Confirm ClickHouse vector server responds to ping"""
        http_get_helper(self, "http://localhost:8123/ping")

    def test_vector_server_version(self):
        """Confirm ClickHouse vector server can list version"""
        sql = quote("select version()")
        basic_auth = generate_basic_auth_header("root", "topsecret")
        http_get_helper(self, f"http://localhost:8123?query={sql}", auth_header=basic_auth)

    def test_iceberg_python_scripts(self):
        """Confirm that iceberg py scripts run without errors"""
        run_python_script_helper(self, "iceberg_setup.py")
        run_python_script_helper(self, "iceberg_read.py")


if __name__ == "__main__":
    unittest.main(verbosity=2)
