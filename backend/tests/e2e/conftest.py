# backend/tests/e2e/conftest.py
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring Azure OpenAI credentials")
