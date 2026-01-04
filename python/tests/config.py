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

import os
from dataclasses import dataclass, fields

import yaml


@dataclass
class TestConfig:
    """Configuration for test environment."""

    ch_host: str
    ch_port: int
    ch_user: str
    ch_password: str
    ice_rest_host: str
    ice_rest_port: int
    ice_config: str
    ice_setting_auth_header: str
    ice_setting_storage_endpoint: str
    ice_setting_warehouse: str
    use_docker: bool


@dataclass
class TestPaths:
    """Paths used by test framework."""

    tests_dir: str
    python_dir: str
    repo_root: str
    docker_dir: str


_config: TestConfig = None
_paths: TestPaths = None


def _convert_value(value: str, field_type: type):
    """Convert string value to the appropriate type."""
    if field_type == bool:
        return value.lower() in ("true", "1", "yes")
    elif field_type == int:
        return int(value)
    return value


def load_config(profile_name: str = None) -> (str, TestConfig):
    """Load config from YAML file and cache it.

    After loading, any value can be overridden by an environment
    variable with the same name in uppercase.
    """
    global _config
    profile_name = profile_name or os.getenv("TEST_PROFILE", "docker")
    config_path = os.path.join(os.path.dirname(__file__), "test_profiles.yaml")

    with open(config_path) as f:
        profiles = yaml.safe_load(f)

    if profile_name not in profiles:
        raise ValueError(
            f"Unknown profile name: {profile_name}. Available: {list(profiles.keys())}"
        )

    _config = TestConfig(**profiles[profile_name])
    print(f"Loaded test profile: {profile_name}")

    # Override with environment variables if present
    for field in fields(TestConfig):
        env_name = field.name.upper()
        env_value = os.getenv(env_name)
        if env_value is not None:
            converted = _convert_value(env_value, field.type)
            setattr(_config, field.name, converted)
            print(f"Override {field.name} from environment variable {env_name}")

    return profile_name, _config


def get_config() -> TestConfig:
    """Get cached config, loading default if needed."""
    if _config is None:
        load_config()
    return _config


def init_paths() -> TestPaths:
    """Compute and cache paths based on this file's location."""
    global _paths
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    python_dir = os.path.dirname(tests_dir)
    repo_root = os.path.dirname(python_dir)
    docker_dir = os.path.join(repo_root, "docker")

    _paths = TestPaths(
        tests_dir=tests_dir,
        python_dir=python_dir,
        repo_root=repo_root,
        docker_dir=docker_dir,
    )
    print(f"Initialized paths: tests={tests_dir}")
    return _paths


def get_paths() -> TestPaths:
    """Get cached paths, initializing if needed."""
    if _paths is None:
        init_paths()
    return _paths
