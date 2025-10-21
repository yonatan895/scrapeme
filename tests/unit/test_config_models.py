"""Unit tests for configuration models."""
from __future__ import annotations

import pytest
from config.models import (
    FieldConfig,
    FrameSpec,
    StepBlock,
    SiteConfig,
    LoginConfig,
)


class TestFieldConfig:
    """Test FieldConfig validation."""
    
    def test_valid_field_config(self):
        """Test valid field configuration."""
        field = FieldConfig(name="title", xpath="//h1")
        assert field.name == "title"
        assert field.xpath == "//h1"
        assert field.attribute is None
    
    def test_field_with_attribute(self):
        """Test field with attribute extraction."""
        field = FieldConfig(name="link", xpath="//a", attribute="href")
        assert field.attribute == "href"
    
    def test_empty_name_raises(self):
        """Test empty field name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            FieldConfig(name="", xpath="//div")
    
    def test_empty_xpath_raises(self):
        """Test empty xpath raises error."""
        with pytest.raises(ValueError, match="xpath cannot be empty"):
            FieldConfig(name="test", xpath="")


class TestFrameSpec:
    """Test FrameSpec validation."""
    
    def test_xpath_selector(self):
        """Test frame spec with XPath."""
        frame = FrameSpec(xpath="//iframe[@id='main']")
        assert frame.xpath == "//iframe[@id='main']"
    
    def test_css_selector(self):
        """Test frame spec with CSS."""
        frame = FrameSpec(css="iframe.content")
        assert frame.css == "iframe.content"
    
    def test_index_selector(self):
        """Test frame spec with index."""
        frame = FrameSpec(index=0)
        assert frame.index == 0
    
    def test_name_selector(self):
        """Test frame spec with name."""
        frame = FrameSpec(name="mainFrame")
        assert frame.name == "mainFrame"
    
    def test_no_selector_raises(self):
        """Test no selector raises error."""
        with pytest.raises(ValueError, match="at least one selector"):
            FrameSpec()
    
    def test_multiple_selectors_raises(self):
        """Test multiple selectors raises error."""
        with pytest.raises(ValueError, match="exactly one selector"):
            FrameSpec(xpath="//iframe", css="iframe")
    
    def test_negative_index_raises(self):
        """Test negative index raises error."""
        with pytest.raises(ValueError, match="non-negative"):
            FrameSpec(index=-1)


class TestStepBlock:
    """Test StepBlock validation."""
    
    def test_valid_step(self, sample_field_config):
        """Test valid step block."""
        step = StepBlock(name="homepage", fields=(sample_field_config,))
        assert step.name == "homepage"
        assert len(step.fields) == 1
    
    def test_empty_name_raises(self):
        """Test empty step name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            StepBlock(name="")
    
    def test_duplicate_field_names_raises(self):
        """Test duplicate field names raises error."""
        field1 = FieldConfig(name="title", xpath="//h1")
        field2 = FieldConfig(name="title", xpath="//h2")
        
        with pytest.raises(ValueError, match="Duplicate field names"):
            StepBlock(name="test", fields=(field1, field2))
    
    def test_invalid_frame_exit_raises(self):
        """Test invalid frame_exit raises error."""
        with pytest.raises(ValueError, match="Invalid frame_exit"):
            StepBlock(name="test", frame_exit="invalid")  # type: ignore


class TestSiteConfig:
    """Test SiteConfig validation."""
    
    def test_valid_site_config(self, sample_step_block):
        """Test valid site configuration."""
        site = SiteConfig(
            name="test_site",
            base_url="https://example.com",
            steps=(sample_step_block,),
        )
        assert site.name == "test_site"
        assert site.base_url == "https://example.com"
    
    def test_empty_name_raises(self):
        """Test empty site name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            SiteConfig(name="", base_url="https://example.com")
    
    def test_negative_timeout_raises(self):
        """Test negative timeout raises error."""
        with pytest.raises(ValueError, match="must be positive"):
            SiteConfig(
                name="test",
                base_url="https://example.com",
                wait_timeout_sec=-1,
            )
    
    def test_duplicate_step_names_raises(self):
        """Test duplicate step names raises error."""
        step1 = StepBlock(name="test", fields=())
        step2 = StepBlock(name="test", fields=())
        
        with pytest.raises(ValueError, match="Duplicate step names"):
            SiteConfig(
                name="site",
                base_url="https://example.com",
                steps=(step1, step2),
            )
    
    def test_total_fields_property(self, sample_field_config):
        """Test total_fields property."""
        step1 = StepBlock(name="step1", fields=(sample_field_config,))
        step2 = StepBlock(name="step2", fields=(sample_field_config, sample_field_config))
        
        site = SiteConfig(
            name="test",
            base_url="https://example.com",
            steps=(step1, step2),
        )
        assert site.total_fields == 3
    
    def test_has_login_property(self, sample_login_config):
        """Test has_login property."""
        site_with_login = SiteConfig(
            name="test",
            base_url="https://example.com",
            login=sample_login_config,
        )
        site_without_login = SiteConfig(
            name="test",
            base_url="https://example.com",
        )
        
        assert site_with_login.has_login is True
        assert site_without_login.has_login is False
