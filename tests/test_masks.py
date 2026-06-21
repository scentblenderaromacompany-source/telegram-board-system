"""
Tests for mask system.
"""
import pytest
from src.masks.mask_registry import MaskRegistry, Mask, MaskType
from src.masks.mask_manager import MaskManager
from src.masks.mask_templates import MaskTemplateLibrary
import tempfile
import os

def test_mask_type():
    assert MaskType.SUPPORT.value == "support"
    assert MaskType.SALES.value == "sales"

def test_mask_creation():
    mask = Mask(
        mask_id="test",
        name="Test Mask",
        mask_type=MaskType.SUPPORT,
        business_id="biz",
        display_name="Test",
    )
    assert mask.mask_id == "test"

def test_mask_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "test.json")
        registry = MaskRegistry(state_file)
        mask = Mask(
            mask_id="test",
            name="Test",
            mask_type=MaskType.SUPPORT,
            business_id="biz",
            display_name="Test",
        )
        registry.register(mask)
        loaded = registry.get("test")
        assert loaded is not None

def test_mask_templates():
    templates = MaskTemplateLibrary.list_templates()
    assert "customer_support" in templates
    assert "jewelry_expert" in templates

def test_mask_template_creation():
    mask = MaskTemplateLibrary.create_mask_from_template(
        mask_id="test",
        name="Test",
        business_id="biz",
        template_name="jewelry_expert",
    )
    assert mask.mask_type == MaskType.CUSTOM
    assert mask.response_style == "heritage"
