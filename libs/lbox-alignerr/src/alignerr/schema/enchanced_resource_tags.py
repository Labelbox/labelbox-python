from enum import Enum
from typing import List, Optional
from labelbox.orm.db_object import DbObject, Updateable
from labelbox.orm.model import Field
from pydantic import BaseModel


class ResourceTagType(Enum):
    """Enum for resource tag types."""

    Default = "Default"
    Billing = "Billing"


class CreateResourceTagInput(BaseModel):
    """Input for creating a new resource tag."""

    text: str
    color: str
    type: Optional[str] = None


class UpdateResourceTagInput(BaseModel):
    """Input for updating a resource tag."""

    id: str
    text: str
    color: str
    type: Optional[str] = None


class DeleteResourceTagInput(BaseModel):
    """Input for deleting a resource tag."""

    id: str
    type: Optional[str] = None


class ResourceTagsInput(BaseModel):
    """Input for querying resource tags."""

    type: str


class EnhancedResourceTag(DbObject, Updateable):
    """Enhanced resource tag with additional functionality and type support."""

    # Fields matching the DDL schema
    id = Field.String("id")
    createdAt = Field.DateTime("createdAt")
    updatedAt = Field.DateTime("updatedAt")
    organizationId = Field.String("organizationId")
    text = Field.String("text")
    color = Field.String("color")
    createdById = Field.String("createdById")
    type = Field.String("type")

    @classmethod
    def create(
        cls,
        client,
        text: str,
        color: str,
        tag_type: Optional[ResourceTagType] = None,
    ) -> "EnhancedResourceTag":
        """Create a new enhanced resource tag.

        Args:
            client: Labelbox client instance
            text: Text content of the resource tag
            color: Color of the resource tag
            tag_type: Optional type of the resource tag

        Returns:
            Created EnhancedResourceTag instance
        """
        # Use the existing organization create_resource_tag method
        # Get the organization
        org = client.get_organization()

        # Create the tag using existing API
        tag_data = {"text": text, "color": color}
        created_tag = org.create_resource_tag(tag_data)

        # Create EnhancedResourceTag with the same data plus defaults for missing fields
        enhanced_tag = cls(
            client,
            {
                "id": created_tag.uid,
                "text": created_tag.text,
                "color": created_tag.color,
                "createdAt": None,
                "updatedAt": None,
                "organizationId": None,
                "createdById": None,
                "type": tag_type.value if tag_type else None,
            },
        )

        return enhanced_tag

    @classmethod
    def search_by_text(
        cls, client, search_text: str, tag_type: ResourceTagType
    ) -> List["EnhancedResourceTag"]:
        """Search resource tags by text content.

        Args:
            client: Labelbox client instance
            search_text: Text to search for
            tag_type: Type filter

        Returns:
            List of matching EnhancedResourceTag instances
        """
        # Use the existing organization get_resource_tags method
        # Get the organization
        org = client.get_organization()

        # Get all resource tags
        regular_tags = org.get_resource_tags()

        # Convert to EnhancedResourceTag instances and filter by search text and type
        matching_tags = []
        for tag in regular_tags:
            if search_text.lower() in tag.text.lower():
                enhanced_tag = cls(
                    client,
                    {
                        "id": tag.uid,
                        "text": tag.text,
                        "color": tag.color,
                        "createdAt": None,
                        "updatedAt": None,
                        "organizationId": None,
                        "createdById": None,
                        "type": tag_type.value,
                    },
                )

                # Apply type filter
                if enhanced_tag.type == tag_type.value:
                    matching_tags.append(enhanced_tag)

        return matching_tags
