import json
import warnings
from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional

from lbox.exceptions import (
    LabelboxError,
    ResourceNotFoundError,
)

from labelbox import Client
from labelbox.pagination import PaginatedCollection


@dataclass
class UploadReportLine:
    """A single line in the CSV report of the upload members mutation.
    Both errors and successes are reported here.

    Example output when using dataclasses.asdict():
    >>> {
    >>>     'lines': [
    >>>         {
    >>>             'email': '...',
    >>>             'result': 'Not added',
    >>>             'error': 'User not found in the current organization'
    >>>         },
    >>>         {
    >>>             'email': '...',
    >>>             'result': 'Not added',
    >>>             'error': 'Member already exists in group'
    >>>         },
    >>>         {
    >>>             'email': '...',
    >>>             'result': 'Added',
    >>>             'error': ''
    >>>         }
    >>>     ]
    >>> }
    """

    email: str
    result: str
    error: Optional[str] = None


@dataclass
class UploadReport:
    """The report of the upload members mutation."""

    lines: List[UploadReportLine]


@dataclass
class Member:
    """A member of a user group."""

    email: str


class UserGroupV2:
    """Upload members to a user group."""

    def __init__(self, client: Client):
        self.client = client

    def upload_members(
        self, group_id: str, role: str, emails: List[str]
    ) -> Optional[UploadReport]:
        """Upload members to a user group.

        Args:
            group_id: A valid ID of the user group.
            role: The name of the role to assign to the uploaded members as it appears in the UI on the Import Members popup.
            emails: The list of emails of the members to upload.

        Returns:
            UploadReport: The report of the upload members mutation.

        Raises:
            ResourceNotFoundError: If the role is not found.
            LabelboxError: If the upload fails.

            For indicvidual email errors, the error message is available in the UploadReport.
        """
        warnings.warn(
            "The upload_members for UserGroupV2 is in beta. The method name and signature may change in the future.”",
        )

        if len(emails) == 0:
            print("No emails to upload.")
            return None

        role_id = self._get_role_id(role)
        if role_id is None:
            raise ResourceNotFoundError(
                message="Could not find a valid role with the name provided. Please make sure the role name is correct."
            )

        buffer = BytesIO()
        buffer.write(b"email\n")  # Header row
        for email in emails:
            buffer.write(f"{email}\n".encode("utf-8"))
        # Reset pointer to start of stream
        buffer.seek(0)

        # Use 0-based indexing as per common convention
        multipart_file_field = "0"
        gql_file_field = "file"

        # Prepare the file content
        files = {
            multipart_file_field: (
                "members.csv",  # More descriptive filename
                buffer,
                "text/csv",
            )
        }
        query = """mutation ImportMembersToGroupPyPi(
                    $roleId: ID!
                    $file: Upload!
                    $where: WhereUniqueIdInput!
                    ) {
                    importUsersAsCsvToGroup(roleId: $roleId, file: $file, where: $where) {
                        csvReport
                        addedCount
                        count
                    }
                }
            """
        # Construct the multipart request following the spec
        operations = {
            "query": query,
            "variables": {
                "roleId": role_id,
                gql_file_field: None,  # Placeholder for file
                "where": {"id": group_id},
            },
        }

        # Map file to the variable
        map_data = {multipart_file_field: [f"variables.{gql_file_field}"]}

        request_data = {
            "operations": json.dumps(operations),
            "map": json.dumps(
                map_data
            ),  # Remove the unnecessary (None, ...) tuple
        }

        file_data = self.client.execute(data=request_data, files=files)

        if not file_data or not file_data.get("importUsersAsCsvToGroup", None):
            error_msg = "Unknown error"
            raise LabelboxError("Failed to upload, message: %s" % error_msg)

        csv_report = file_data["importUsersAsCsvToGroup"]["csvReport"]
        return self._parse_csv_report(csv_report)

    def export_members(self, group_id: str) -> Optional[List[Member]]:
        warnings.warn(
            "The export_members for UserGroupV2 is in beta. The method name and signature may change in the future.",
        )

        if not group_id:
            raise ValueError("Group id is required")

        query = """query GetExportMembersAsCSVPyPi(
            $id: ID!
            ) {
            userGroupV2(where: { id: $id }) {
                id
                membersAsCSV
            }
        }
        """
        params = {
            "id": group_id,
        }

        result = self.client.execute(query, params)
        if result["userGroupV2"] is None:
            raise ResourceNotFoundError(message="The user group is not found.")
        data = result["userGroupV2"]

        return self._parse_members_csv(data["membersAsCSV"])

    def _parse_members_csv(self, csv_data: str) -> List[Member]:
        csv_lines = csv_data.strip().split("\n")
        if not csv_lines:
            return []

        members_list = []
        # Skip header row
        for email in csv_lines[1:]:
            if email.strip():  # Skip empty lines
                members_list.append(Member(email=email.strip()))

        return members_list

    def _get_role_id(self, role_name: str) -> Optional[str]:
        role_id = None
        query = """query GetAvailableUserRolesPyPi {
                    roles(skip: %d, first: %d) {
                        id
                        organizationId
                        name
                        description
                    }
                }
            """

        result = PaginatedCollection(
            client=self.client,
            query=query,
            params={},
            dereferencing=["roles"],
            obj_class=lambda _, data: data,  # type: ignore
        )
        if result is None:
            raise ResourceNotFoundError(
                message="Could not find any valid roles."
            )
        for role in result:
            if role["name"].strip() == role_name.strip():
                role_id = role["id"]
                break

        return role_id

    def _parse_csv_report(self, csv_report: str) -> UploadReport:
        lines = csv_report.strip().split("\n")
        headers = lines[0].split(",")
        report_lines = []
        for line in lines[1:]:
            values = line.split(",")
            row = dict(zip(headers, values))
            report_lines.append(
                UploadReportLine(
                    email=row["Email"],
                    result=row["Result"],
                    error=row.get(
                        "Error"
                    ),  # Using get() since error is optional
                )
            )
        return UploadReport(lines=report_lines)
