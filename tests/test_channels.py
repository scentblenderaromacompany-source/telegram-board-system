"""
Tests for channel system.
"""
import pytest
from src.channels.channel_registry import ChannelRegistry, Channel, ChannelType, ChannelStatus
from src.channels.channel_manager import ChannelManager
from src.channels.message_router import MessageRouter
import tempfile
import os

def test_channel_type():
    assert ChannelType.BROADCAST.value == "broadcast"
    assert ChannelType.SUPPORT.value == "support"

def test_channel_status():
    assert ChannelStatus.ACTIVE.value == "active"

def test_channel_creation():
    ch = Channel(
        channel_id="test",
        name="Test Channel",
        business_id="test-business",
        channel_type=ChannelType.SUPPORT,
    )
    assert ch.channel_id == "test"
    assert ch.status == ChannelStatus.ACTIVE

def test_channel_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "test.json")
        registry = ChannelRegistry(state_file)
        ch = Channel(
            channel_id="test",
            name="Test",
            business_id="biz",
            channel_type=ChannelType.SUPPORT,
        )
        registry.register(ch)
        loaded = registry.get("test")
        assert loaded is not None
        assert loaded.name == "Test"

def test_channel_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "test.json")
        registry = ChannelRegistry(state_file)
        manager = ChannelManager(registry)
        ch = manager.create_channel(
            channel_id="test",
            name="Test",
            business_id="biz",
            channel_type=ChannelType.SUPPORT,
        )
        assert ch.channel_id == "test"
        assert len(manager.list_channels()) == 1
