import datetime
from typing import TYPE_CHECKING, Union, List
import yaml
from pathlib import Path
import logging

from labelbox.alignerr.schema.project_rate import BillingMode
from labelbox.alignerr.schema.enchanced_resource_tags import ResourceTagType
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
            ValueError: If required fields are missing or invalid

        YAML Configuration Structure:
            name: str (required) - Project name
            media_type: str (required) - Media type (e.g., "Image", "Video", "Text")
            rates: dict (optional) - Alignerr role rates
                role_name:
                    rate: float
                    billing_mode: str
                    effective_since: str (ISO datetime)
                    effective_until: str (optional, ISO datetime)
            customer_rate: dict (optional) - Customer billing rate
                rate: float
                billing_mode: str
                effective_since: str (ISO datetime)
                effective_until: str (optional, ISO datetime)
            domains: list[str] (optional) - Project domain names
            tags: list[dict] (optional) - Enhanced resource tags
                - text: str
                  type: str (ResourceTagType enum value)
            project_owner: str (optional) - Project owner email address
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

        # Import here to avoid circular imports
        from labelbox.alignerr.alignerr_project_builder import (
            AlignerrProjectBuilder,
        )
        from labelbox.alignerr.alignerr_project import AlignerrRole

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

        # Set project rates if provided
        if "rates" in config:
            rates_config = config["rates"]
            if not isinstance(rates_config, dict):
                raise ValueError("'rates' must be a dictionary")

            for role_name, rate_config in rates_config.items():
                try:
                    alignerr_role = AlignerrRole(role_name.upper())
                except ValueError:
                    raise ValueError(
                        f"Invalid role '{role_name}'. Must be one of: {[r.value for r in AlignerrRole]}"
                    )

                # Validate rate configuration
                required_rate_fields = [
                    "rate",
                    "billing_mode",
                    "effective_since",
                ]
                for field in required_rate_fields:
                    if field not in rate_config:
                        raise ValueError(
                            f"Required field '{field}' is missing for role '{role_name}'"
                        )

                # Parse billing mode
                try:
                    billing_mode = BillingMode(rate_config["billing_mode"])
                except ValueError:
                    raise ValueError(
                        f"Invalid billing_mode '{rate_config['billing_mode']}' for role '{role_name}'. Must be one of: {[e.value for e in BillingMode]}"
                    )

                # Parse effective dates
                try:
                    effective_since = datetime.datetime.fromisoformat(
                        rate_config["effective_since"]
                    )
                except ValueError:
                    raise ValueError(
                        f"Invalid effective_since date format for role '{role_name}'. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                    )

                effective_until = None
                if (
                    "effective_until" in rate_config
                    and rate_config["effective_until"]
                ):
                    try:
                        effective_until = datetime.datetime.fromisoformat(
                            rate_config["effective_until"]
                        )
                    except ValueError:
                        raise ValueError(
                            f"Invalid effective_until date format for role '{role_name}'. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                        )

                # Set the rate
                builder.set_alignerr_role_rate(
                    role_name=alignerr_role,
                    rate=float(rate_config["rate"]),
                    billing_mode=billing_mode,
                    effective_since=effective_since,
                    effective_until=effective_until,
                )

        # Set customer rate if provided
        if "customer_rate" in config:
            customer_rate_config = config["customer_rate"]
            if not isinstance(customer_rate_config, dict):
                raise ValueError("'customer_rate' must be a dictionary")

            # Validate customer rate configuration
            required_customer_rate_fields = [
                "rate",
                "billing_mode",
                "effective_since",
            ]
            for field in required_customer_rate_fields:
                if field not in customer_rate_config:
                    raise ValueError(
                        f"Required field '{field}' is missing for customer_rate"
                    )

            # Parse billing mode
            try:
                billing_mode = BillingMode(customer_rate_config["billing_mode"])
            except ValueError:
                raise ValueError(
                    f"Invalid billing_mode '{customer_rate_config['billing_mode']}' for customer_rate. Must be one of: {[e.value for e in BillingMode]}"
                )

            # Parse effective dates
            try:
                effective_since = datetime.datetime.fromisoformat(
                    customer_rate_config["effective_since"]
                )
            except ValueError:
                raise ValueError(
                    f"Invalid effective_since date format for customer_rate. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )

            effective_until = None
            if (
                "effective_until" in customer_rate_config
                and customer_rate_config["effective_until"]
            ):
                try:
                    effective_until = datetime.datetime.fromisoformat(
                        customer_rate_config["effective_until"]
                    )
                except ValueError:
                    raise ValueError(
                        f"Invalid effective_until date format for customer_rate. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                    )

            # Set the customer rate
            builder.set_customer_rate(
                rate=float(customer_rate_config["rate"]),
                billing_mode=billing_mode,
                effective_since=effective_since,
                effective_until=effective_until,
            )

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
                        raise ValueError(
                            f"Required field '{field}' is missing for tag"
                        )
                
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
