import json
import warnings
from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional

import requests
from lbox.exceptions import (
    InternalServerError,
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

        multipart_file_field = "1"
        gql_file_field = "file"
        files = {
            multipart_file_field: (
                f"{multipart_file_field}.csv",
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
        params = {
            "roleId": role_id,
            gql_file_field: None,
            "where": {"id": group_id},
        }

        request_data = {
            "operations": json.dumps(
                {
                    "variables": params,
                    "query": query,
                }
            ),
            "map": (
                None,
                json.dumps(
                    {multipart_file_field: [f"variables.{gql_file_field}"]}
                ),
            ),
        }

        client = self.client
        headers = dict(client.connection.headers)
        headers.pop("Content-Type", None)
        request = requests.Request(
            "POST",
            client.endpoint,
            headers=headers,
            data=request_data,
            files=files,
        )

        prepped: requests.PreparedRequest = request.prepare()

        response = client.connection.send(prepped)

        if response.status_code == 502:
            error_502 = "502 Bad Gateway"
            raise InternalServerError(error_502)
        elif response.status_code == 503:
            raise InternalServerError(response.text)
        elif response.status_code == 520:
            raise InternalServerError(response.text)

        try:
            file_data = response.json().get("data", None)
        except ValueError as e:  # response is not valid JSON
            raise LabelboxError("Failed to upload, unknown cause", e)

        if not file_data or not file_data.get("importUsersAsCsvToGroup", None):
            try:
                errors = response.json().get("errors", [])
                error_msg = "Unknown error"
                if errors:
                    error_msg = errors[0].get("message", "Unknown error")
            except Exception:
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
