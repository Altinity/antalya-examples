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

import unittest

from config import init_paths, load_config
from helpers import ClickHouseHelper, DockerHelper, OsHelper


class AntalyaTestFramework(unittest.TestCase):
    """Framework to test Antalya example setups."""

    docker_helper: DockerHelper = None
    clickhouse_helper: ClickHouseHelper = None
    os_helper: OsHelper = None
    profile_name: str = None
    config: str = None

    @classmethod
    def setUpClass(cls):
        """Compute test parameters and optionally manage Docker services."""
        (cls.profile_name, cls.config) = load_config()
        paths = init_paths()

        if cls.config.use_docker:
            cls.docker_helper = DockerHelper(cls.config, paths)
            cls.docker_helper.setup_services()
        cls.clickhouse_helper = ClickHouseHelper(cls.config, paths)
        cls.os_helper = OsHelper(cls.config, paths)

    @classmethod
    def tearDownClass(cls):
        """Capture logs and stop Docker Compose services if we started them."""
        if cls.docker_helper:
            cls.docker_helper.cleanup_services()

    def test_ice_catalog_liveness(self):
        """Confirm ice catalog on 5000 can list namespaces."""
        self.os_helper.http_get(
            self, "http://localhost:5000/v1/namespaces", auth_header="Bearer foo"
        )

    def test_vector_server_liveness(self):
        """Confirm ClickHouse vector server responds to ping."""
        self.os_helper.http_get(self, "http://localhost:8123/ping")

    def test_vector_server_version(self):
        """Confirm ClickHouse vector server can list version."""
        from urllib.parse import quote

        sql = quote("select version()")
        basic_auth = self.os_helper.generate_basic_auth_header("root", "topsecret")
        self.os_helper.http_get(
            self, f"http://localhost:8123?query={sql}", auth_header=basic_auth
        )

    def test_iceberg_python_scripts(self):
        """Confirm that iceberg py scripts run without errors."""
        # FIXME: Scripts need to be fixed to run on Kubernetes as well as Docker"
        if self.config.use_docker:
            self.os_helper.run_python_script(self, "iceberg_setup.py")
            self.os_helper.run_python_script(self, "iceberg_read.py")
        else:
            print("FIXME: Test case skipped for non-docker environments")

    def test_clickhouse_vector_server_connection(self):
        """Test ClickHouse connection using clickhouse-driver on port 9000."""
        result = self.clickhouse_helper.query(self, "SELECT version()")
        version = result.get("version()")

        self.assertIsNotNone(version)
        print(f"ClickHouse version: {version}")

    def test_ice_database_show_tables(self):
        """Verify we can create an Ice catalog database and show tables."""
        # Create a test Ice catalog database in ClickHouse, dropping it first.
        catalog_created = self.clickhouse_helper.create_iceberg_rest_catalog(
            self, "ice_test", True
        )
        self.clickhouse_helper.query(self, "show tables from ice_test")

    def test_load_ice_and_select(self):
        """Verify we can load a file to Ice catalog and read from ClickHouse."""
        # Create a test Ice catalog database in ClickHouse, dropping it first.
        catalog_created = self.clickhouse_helper.create_iceberg_rest_catalog(
            self, "ice_test", True
        )
        assert catalog_created

        # Remove test table if it existed.
        self.os_helper.run_ice_command(
            self,
            ice_command=[
                "delete-table",
                "--purge",
                "nyc.taxis_test",
            ],
            ignore_returncode=True,
        )

        # Create the table from scratch.
        self.os_helper.run_ice_command(
            self,
            ice_command=[
                "insert",
                "nyc.taxis_test",
                "-p",
                "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet",
            ],
            expected_output="Committed snapshot",
            expected_returncode=0,
        )

        # Create a test iceberg catalog database in ClickHouse, dropping it first.
        catalog_created = self.clickhouse_helper.create_iceberg_rest_catalog(
            self, "ice_test", True
        )
        assert catalog_created

        # Issue a query to check stats. Number must be greater than 0.
        vector_query = """
        SELECT
            count() AS count,
            avg(passenger_count) AS passengers,
            avg(fare_amount) AS fare
        FROM ice_test.`nyc.taxis_test`
        """
        vector_result = self.clickhouse_helper.query(self, vector_query)
        assert "count" in vector_result
        assert vector_result["count"] > 0

        # Issue a query to count rows again using the swarm.
        swarm_query = vector_query + " SETTINGS object_storage_cluster='swarm'"
        swarm_result = self.clickhouse_helper.query(self, swarm_query)
        assert "count" in swarm_result
        assert swarm_result["count"] > 0
        assert swarm_result["count"] == vector_result["count"]
        print(
            f"Swarm count {swarm_result['count']} equals vector count {vector_result['count']}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
