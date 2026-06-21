"""
conftest.py - provides event loop for all async tests.
"""
import asyncio
import pytest


@pytest.fixture
def event_loop():
    """Create event loop for each async test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
