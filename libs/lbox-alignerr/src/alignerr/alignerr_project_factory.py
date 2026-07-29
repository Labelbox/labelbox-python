from typing import TYPE_CHECKING, Union, List
import yaml
from pathlib import Path
import logging

from alignerr.alignerr_project import PAY_BY_ROLE_REMOVED_MSG
from alignerr.schema.enchanced_resource_tags import ResourceTagType
from labelbox.schema.media_type import MediaType

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from labelbox import Client


class AlignerrProjectFactory:
    def __init__(self, client: "Client"):
        self.client = client

    def create(self, yaml_file_path: str, skip_validation: Union[bool, List] = False):
        """
        Create an AlignerrProject from a YAML configuration file.

        Args:
            yaml_file_path: Path to the YAML configuration file
            skip_validation: Whether to skip validation of required fields. Can be:
                - bool: Skip all validations (True) or run all validations (False)
                - List: Skip specific validations (e.g., [ValidationType.PROJECT_OWNER])

        Returns:
            AlignerrProject: The created project with all configured attributes

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If required fields are missing or invalid, or if legacy
                rates / customer_rate keys are present

        YAML Configuration Structure:
            name: str (required) - Project name
            media_type: str (required) - Media type (e.g., "Image", "Video", "Text")
            domains: list[str] (optional) - Project domain names
            tags: list[dict] (optional) - Enhanced resource tags
                - text: str
                  type: str (ResourceTagType enum value)
            project_owner: str (optional) - Project owner email address

        Note:
            Legacy `rates` and `customer_rate` YAML keys are no longer supported.
            Configure rates in the Labelbox Rates UI (Pay By Activity).
        """
        logger.info(f"Creating project from YAML file: {yaml_file_path}")

        # Load and parse YAML file
        yaml_path = Path(yaml_file_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file_path}")

        try:
            with open(yaml_path, "r") as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML file: {e}")

        # Validate required fields
        if not config:
            raise ValueError("YAML file is empty")

        required_fields = ["name", "media_type"]
        for field in required_fields:
            if field not in config:
                raise ValueError(
                    f"Required field '{field}' is missing from YAML configuration"
                )

        if "rates" in config or "customer_rate" in config:
            raise ValueError(PAY_BY_ROLE_REMOVED_MSG)

        # Import here to avoid circular imports
        from alignerr.alignerr_project_builder import (
            AlignerrProjectBuilder,
        )

        # Create project builder
        builder = AlignerrProjectBuilder(self.client)

        # Set basic project properties
        builder.set_name(config["name"])

        # Set media type
        media_type_str = config["media_type"]
        media_type = MediaType(media_type_str)

        # Check if the media type is supported
        if not MediaType.is_supported(media_type):
            supported_members = MediaType.get_supported_members()
            raise ValueError(
                f"Invalid media_type '{media_type_str}'. Must be one of: {supported_members}"
            )

        builder.set_media_type(media_type)

        # Set domains if provided
        if "domains" in config:
            domains_config = config["domains"]
            if not isinstance(domains_config, list):
                raise ValueError("'domains' must be a list")

            if not all(isinstance(domain, str) for domain in domains_config):
                raise ValueError("All domain names must be strings")

            builder.set_domains(domains_config)

        # Set enhanced resource tags if provided
        if "tags" in config:
            tags_config = config["tags"]
            if not isinstance(tags_config, list):
                raise ValueError("'tags' must be a list")

            for tag_config in tags_config:
                if not isinstance(tag_config, dict):
                    raise ValueError("Each tag must be a dictionary")

                required_tag_fields = ["text", "type"]
                for field in required_tag_fields:
                    if field not in tag_config:
                        raise ValueError(f"Required field '{field}' is missing for tag")

                # Validate tag type
                try:
                    tag_type = ResourceTagType(tag_config["type"])
                except ValueError:
                    raise ValueError(
                        f"Invalid tag type '{tag_config['type']}'. Must be one of: {[e.value for e in ResourceTagType]}"
                    )

                # Set the tag
                builder.set_tags([tag_config["text"]], tag_type)

        # Set project owner if provided
        if "project_owner" in config:
            project_owner_config = config["project_owner"]
            if not isinstance(project_owner_config, str):
                raise ValueError("'project_owner' must be a string (email address)")

            builder.set_project_owner(project_owner_config)

        # Create the project
        return builder.create(skip_validation=skip_validation)
