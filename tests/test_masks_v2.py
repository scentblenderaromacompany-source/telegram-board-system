"""
Comprehensive isolated tests for src/masks/ module.
"""
import json

import pytest

from src.masks.mask_registry import MaskRegistry, Mask, MaskType
from src.masks.mask_manager import MaskManager
from src.masks.mask_templates import MaskTemplateLibrary
from src.masks.persona_engine import PersonaEngine


class TestMaskType:
    def test_values(self):
        assert MaskType.SUPPORT.value == "support"
        assert MaskType.SALES.value == "sales"
        assert MaskType.CONTENT.value == "content"
        assert MaskType.MONITOR.value == "monitor"
        assert MaskType.CUSTOM.value == "custom"


class TestMask:
    def test_creation(self):
        m = Mask(
            mask_id="m1",
            name="Support",
            mask_type=MaskType.SUPPORT,
            business_id="biz",
            display_name="SupportBot",
        )
        assert m.mask_id == "m1"
        assert m.mask_type == MaskType.SUPPORT
        assert m.response_style == "professional"
        assert m.emoji_enabled is True

    def test_defaults(self):
        m = Mask(
            mask_id="m1",
            name="Test",
            mask_type=MaskType.CUSTOM,
            business_id="biz",
            display_name="TestBot",
        )
        assert m.avatar_url is None
        assert m.bio == ""
        assert m.sticker_packs == []
        assert m.vocabulary == []
        assert m.restricted_words == []


class TestMaskRegistry:
    def test_empty(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        assert len(reg._masks) == 0

    def test_register(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        m = Mask(
            mask_id="m1",
            name="Test",
            mask_type=MaskType.SUPPORT,
            business_id="biz",
            display_name="TestBot",
        )
        reg.register(m)
        assert reg.get("m1") is m

    def test_register_persists(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg1 = MaskRegistry(str(state_file))
        m = Mask(
            mask_id="m1",
            name="Test",
            mask_type=MaskType.SUPPORT,
            business_id="biz",
            display_name="TestBot",
        )
        reg1.register(m)
        reg2 = MaskRegistry(str(state_file))
        assert reg2.get("m1") is not None

    def test_get_nonexistent(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        assert reg.get("nonexistent") is None

    def test_list_by_business(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        reg.register(Mask(
            mask_id="m1", name="A", mask_type=MaskType.SUPPORT,
            business_id="biz1", display_name="A",
        ))
        reg.register(Mask(
            mask_id="m2", name="B", mask_type=MaskType.SUPPORT,
            business_id="biz2", display_name="B",
        ))
        reg.register(Mask(
            mask_id="m3", name="C", mask_type=MaskType.SUPPORT,
            business_id="biz1", display_name="C",
        ))
        assert len(reg.list_by_business("biz1")) == 2
        assert len(reg.list_by_business("biz2")) == 1

    def test_list_by_type(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        reg.register(Mask(
            mask_id="m1", name="A", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="A",
        ))
        reg.register(Mask(
            mask_id="m2", name="B", mask_type=MaskType.SALES,
            business_id="biz", display_name="B",
        ))
        assert len(reg.list_by_type(MaskType.SUPPORT)) == 1
        assert len(reg.list_by_type(MaskType.SALES)) == 1

    def test_delete(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        reg.register(Mask(
            mask_id="m1", name="A", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="A",
        ))
        assert reg.delete("m1") is True
        assert reg.get("m1") is None

    def test_delete_nonexistent(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        assert reg.delete("nonexistent") is False


class TestMaskManager:
    def test_assign_mask(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="TestBot",
        )
        reg.register(m)
        assert manager.assign_mask("bot1", "m1") is True
        assert manager.get_mask_for_bot("bot1") is m

    def test_assign_nonexistent_mask(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        assert manager.assign_mask("bot1", "nonexistent") is False

    def test_unassign_mask(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="TestBot",
        )
        reg.register(m)
        manager.assign_mask("bot1", "m1")
        manager.unassign_mask("bot1")
        assert manager.get_mask_for_bot("bot1") is None

    def test_get_mask_for_unassigned_bot(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        assert manager.get_mask_for_bot("unassigned") is None

    def test_create_mask(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        m = manager.create_mask(
            mask_id="m1",
            name="Test",
            mask_type=MaskType.SUPPORT,
            business_id="biz",
            display_name="TestBot",
        )
        assert m.mask_id == "m1"
        assert reg.get("m1") is m

    def test_list_masks_all(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        manager.create_mask("m1", "A", MaskType.SUPPORT, "biz1", "A")
        manager.create_mask("m2", "B", MaskType.SALES, "biz2", "B")
        assert len(manager.list_masks()) == 2

    def test_list_masks_by_business(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        manager.create_mask("m1", "A", MaskType.SUPPORT, "biz1", "A")
        manager.create_mask("m2", "B", MaskType.SALES, "biz2", "B")
        assert len(manager.list_masks("biz1")) == 1

    def test_apply_persona(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        manager.create_mask("m1", "Test", MaskType.SUPPORT, "biz", "TestBot")
        manager.assign_mask("bot1", "m1")
        result = manager.apply_persona("bot1", "hello world")
        assert result == "hello world"

    def test_apply_persona_no_mask(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        result = manager.apply_persona("bot1", "hello")
        assert result == "hello"

    def test_set_rotation(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        manager.set_rotation("biz1", ["m1", "m2"])
        assert manager._rotation["biz1"] == ["m1", "m2"]

    def test_get_next_mask(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        manager.create_mask("m1", "A", MaskType.SUPPORT, "biz", "A")
        manager.create_mask("m2", "B", MaskType.SALES, "biz", "B")
        manager.set_rotation("biz", ["m1", "m2"])
        m = manager.get_next_mask("biz")
        assert m is not None
        assert m.mask_id == "m1"

    def test_get_next_mask_empty(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        manager = MaskManager(reg)
        assert manager.get_next_mask("biz") is None


class TestMaskTemplates:
    def test_list_templates(self):
        templates = MaskTemplateLibrary.list_templates()
        assert len(templates) == 6
        assert "customer_support" in templates
        assert "sales_rep" in templates
        assert "jewelry_expert" in templates
        assert "content_creator" in templates
        assert "tech_support" in templates
        assert "monitor_bot" in templates

    def test_get_template(self):
        t = MaskTemplateLibrary.get_template("customer_support")
        assert t["mask_type"] == MaskType.SUPPORT
        assert t["response_style"] == "support"

    def test_get_template_fallback(self):
        t = MaskTemplateLibrary.get_template("nonexistent")
        assert t["mask_type"] == MaskType.SUPPORT

    def test_create_mask_from_template(self):
        m = MaskTemplateLibrary.create_mask_from_template(
            mask_id="m1",
            name="Support Bot",
            business_id="biz",
            template_name="customer_support",
        )
        assert m.mask_id == "m1"
        assert m.mask_type == MaskType.SUPPORT
        assert m.response_style == "support"
        assert m.tone == "helpful"

    def test_create_with_overrides(self):
        m = MaskTemplateLibrary.create_mask_from_template(
            mask_id="m1",
            name="Custom Bot",
            business_id="biz",
            template_name="customer_support",
            tone="formal",
            emoji_enabled=False,
        )
        assert m.tone == "formal"
        assert m.emoji_enabled is False


class TestPersonaEngine:
    def test_detect_sentiment_positive(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        scores = engine.detect_sentiment("I love this, it's great and awesome!")
        assert scores["positive"] > 0

    def test_detect_sentiment_negative(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        scores = engine.detect_sentiment("I hate this, it's terrible and awful!")
        assert scores["negative"] > 0

    def test_detect_sentiment_question(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        scores = engine.detect_sentiment("How do I use this? What is it?")
        assert scores["question"] > 0

    def test_detect_sentiment_urgent(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        scores = engine.detect_sentiment("This is urgent, need it ASAP immediately!")
        assert scores["urgent"] > 0

    def test_detect_sentiment_confused(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        scores = engine.detect_sentiment("I'm confused, don't understand, unclear")
        assert scores["confused"] > 0

    def test_get_style_template(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        t = engine.get_style_template("professional")
        assert t["tone"] == "formal"
        t = engine.get_style_template("friendly")
        assert t["tone"] == "casual"

    def test_get_style_template_fallback(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        t = engine.get_style_template("nonexistent")
        assert t["tone"] == "formal"

    def test_apply_persona_restricted_words(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="TestBot",
            restricted_words=["badword"],
            response_style="professional",
        )
        result = engine.apply_persona(m, "this has badword in it")
        assert "badword" not in result
        assert "***" in result

    def test_apply_persona_no_restricted_words(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="TestBot",
            response_style="professional",
        )
        result = engine.apply_persona(m, "hello world")
        assert result == "hello world"

    def test_get_greeting(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="SupportBot",
            response_style="professional",
        )
        greeting = engine.get_greeting(m)
        assert "SupportBot" in greeting
        assert "Hello" in greeting

    def test_get_greeting_with_time(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="SupportBot",
            response_style="professional",
        )
        greeting = engine.get_greeting(m, {"time_of_day": 8})
        assert "morning" in greeting.lower()
        greeting = engine.get_greeting(m, {"time_of_day": 14})
        assert "afternoon" in greeting.lower()
        greeting = engine.get_greeting(m, {"time_of_day": 20})
        assert "evening" in greeting.lower()

    def test_get_farewell(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="SupportBot",
            response_style="professional",
        )
        farewell = engine.get_farewell(m)
        assert "SupportBot" in farewell
        assert "Thank" in farewell

    def test_get_fallback(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="SupportBot",
            response_style="professional",
        )
        fallback = engine.get_fallback(m)
        assert "SupportBot" in fallback

    def test_get_fallback_confused(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        m = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="SupportBot",
            response_style="professional",
        )
        fallback = engine.get_fallback(m, {"confused": 0.5})
        assert "confused" in fallback.lower()

    def test_register_style(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        custom = {"greeting": "Hi!", "farewell": "Bye!", "fallback": "What?", "tone": "custom", "emoji": False, "max_length": 4096, "response_style": "custom"}
        engine.register_style("custom", custom)
        assert engine.get_style_template("custom")["tone"] == "custom"

    def test_ab_testing(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        variants = [{"style": "A"}, {"style": "B"}]
        engine.register_ab_variant("test", variants)
        v1 = engine.get_ab_variant("test", 0)
        v2 = engine.get_ab_variant("test", 1)
        assert v1["style"] == "A"
        assert v2["style"] == "B"

    def test_ab_testing_no_variants(self, tmp_path):
        state_file = tmp_path / "masks.json"
        reg = MaskRegistry(str(state_file))
        engine = PersonaEngine(reg)
        assert engine.get_ab_variant("nonexistent", 0) is None
