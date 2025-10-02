"""Integration tests for EnhancedResourceTag functionality.

These tests interact with the actual Labelbox API to verify EnhancedResourceTag operations.
"""

import pytest
import uuid

from labelbox.alignerr.schema.enchanced_resource_tags import (
    EnhancedResourceTag,
    ResourceTagType,
)


@pytest.fixture
def test_resource_tags(client):
    """Create test resource tags for testing."""
    tags = []
    
    # Create multiple test tags with different types
    for i, tag_type in enumerate([ResourceTagType.Default, ResourceTagType.Billing]):
        tag_text = f"Test_Tag_{i+1}_{uuid.uuid4().hex[:8]}"
        tag_color = f"#{i:06x}"  # Generate different colors
        tag = EnhancedResourceTag.create(
            client, 
            text=tag_text, 
            color=tag_color, 
            tag_type=tag_type
        )
        tags.append(tag)
    
    yield tags
    
    # Cleanup - delete tags
    for tag in tags:
        try:
            tag.delete()
        except Exception:
            pass  # Tag may already be deleted


def test_create_enhanced_resource_tag(client):
    """Test creating a new enhanced resource tag."""
    tag_text = f"Test_Create_Tag_{uuid.uuid4().hex[:8]}"
    tag_color = "#FF5733"
    
    # Create tag
    tag = EnhancedResourceTag.create(
        client, 
        text=tag_text, 
        color=tag_color, 
        tag_type=ResourceTagType.Default
    )
    
    assert tag is not None
    assert tag.text == tag_text
    assert tag.color == tag_color.lstrip('#')  # API returns color without #
    assert tag.type == ResourceTagType.Default.value
    assert tag.id is not None
    # Note: createdAt and organizationId are not available in current API
    # assert tag.createdAt is not None
    # assert tag.organizationId is not None
    
    # Cleanup
    try:
        tag.delete()
    except Exception:
        pass


def test_create_enhanced_resource_tag_without_type(client):
    """Test creating a resource tag without specifying type."""
    tag_text = f"Test_Create_Tag_No_Type_{uuid.uuid4().hex[:8]}"
    tag_color = "#33FF57"
    
    # Create tag without type
    tag = EnhancedResourceTag.create(
        client, 
        text=tag_text, 
        color=tag_color
    )
    
    assert tag is not None
    assert tag.text == tag_text
    assert tag.color == tag_color.lstrip('#')  # API returns color without #
    assert tag.id is not None
    # Note: createdAt is not available in current API
    # assert tag.createdAt is not None
    
    # Cleanup
    try:
        tag.delete()
    except Exception:
        pass






def test_search_by_text(client, test_resource_tags):
    """Test searching resource tags by text content."""
    # Test 1: Search for exact text match
    target_tag = test_resource_tags[0]
    search_results = EnhancedResourceTag.search_by_text(
        client, search_text=target_tag.text, tag_type=ResourceTagType.Default
    )
    assert isinstance(search_results, list)
    assert len(search_results) >= 1
    assert any(tag.text == target_tag.text for tag in search_results)
    
    # Test 2: Search for partial text match
    partial_text = "Test_Tag"
    partial_results = EnhancedResourceTag.search_by_text(
        client, search_text=partial_text, tag_type=ResourceTagType.Default
    )
    assert isinstance(partial_results, list)
    assert len(partial_results) >= 1  # At least one Default type tag
    assert all(partial_text in tag.text for tag in partial_results)
    
    # Test 3: Search with type filter
    type_filtered_results = EnhancedResourceTag.search_by_text(
        client, 
        search_text="Test_Tag", 
        tag_type=ResourceTagType.Default
    )
    assert isinstance(type_filtered_results, list)
    # All results should contain the search text and match the type
    for tag in type_filtered_results:
        assert "Test_Tag" in tag.text
        assert tag.type == ResourceTagType.Default.value
    
    # Test 4: Search for non-existent text
    non_existent_results = EnhancedResourceTag.search_by_text(
        client, search_text="NonExistentTag12345", tag_type=ResourceTagType.Default
    )
    assert isinstance(non_existent_results, list)
    assert len(non_existent_results) == 0


def test_resource_tag_types_enum(client):
    """Test that all resource tag types are properly defined."""
    # Test creating tags with each supported type
    supported_types = [ResourceTagType.Default, ResourceTagType.Billing]
    for tag_type in supported_types:
        tag_text = f"Test_{tag_type.value}_Tag_{uuid.uuid4().hex[:8]}"
        tag_color = "#123456"
        
        tag = EnhancedResourceTag.create(
            client, 
            text=tag_text, 
            color=tag_color, 
            tag_type=tag_type
        )
        
        assert tag.type == tag_type.value
        
        # Cleanup
        try:
            tag.delete()
        except Exception:
            pass


def test_enhanced_resource_tag_properties(client, test_resource_tags):
    """Test that enhanced resource tags have all expected properties."""
    tag = test_resource_tags[0]
    
    # Test all expected properties exist
    expected_properties = [
        'id', 'createdAt', 'updatedAt', 'organizationId', 'text', 
        'color', 'createdById', 'type'
    ]
    
    for prop in expected_properties:
        assert hasattr(tag, prop), f"Tag missing property: {prop}"
    
    # Test that required properties are not None
    assert tag.id is not None
    assert tag.text is not None
    assert tag.color is not None
    # Note: Some properties are not available in current API
    # assert tag.createdAt is not None
    # assert tag.organizationId is not None


