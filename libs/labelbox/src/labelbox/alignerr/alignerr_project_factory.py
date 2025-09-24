import datetime
from typing import TYPE_CHECKING
import yaml
from pathlib import Path
import logging

from labelbox.alignerr.schema.project_rate import BillingMode
from labelbox.schema.media_type import MediaType

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from labelbox import Client


class AlignerrProjectFactory:
    def __init__(self, client: "Client"):
        self.client = client

    def create(self, yaml_file_path: str, skip_validation: bool = False):
        """
        Create an AlignerrProject from a YAML configuration file.

        Args:
            yaml_file_path: Path to the YAML configuration file
            skip_validation: Whether to skip validation of required fields

        Returns:
            AlignerrProject: The created project with configured rates

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If required fields are missing or invalid
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

        # Create the project
        return builder.create(skip_validation=skip_validation)
