"""
Pytest configuration for Mindful Touch integration tests
"""

import asyncio
import logging

import pytest

# Configure logging for all tests
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# Configure pytest for asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests (may be slow)")
    config.addinivalue_line("markers", "websocket: marks tests that test websocket functionality")
    config.addinivalue_line("markers", "backend: marks tests that require the detection backend")
    config.addinivalue_line("markers", "slow: marks tests as slow (may take more than 10 seconds)")
