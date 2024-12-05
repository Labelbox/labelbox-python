import json
from io import BytesIO
from typing import List, Optional

import requests
from lbox.exceptions import (
    InternalServerError,
    LabelboxError,
    ResourceNotFoundError,
)

from labelbox.client import Client
from labelbox.pagination import PaginatedCollection


class UserGroupUpload:
    def __init__(self, client: Client):
        self.client = client

    def upload_members(self, group_id: str, role: str, emails: List[str]):
        if len(emails) == 0:
            print("No emails to upload.")
            return

        role_id = self._get_role_id(role)
        if role_id is None:
            raise ResourceNotFoundError(message="The role does not exist.")

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
        query = """mutation ImportMembersToGroup(
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
                error_msg = next(iter(errors), {}).get(
                    "message", "Unknown error"
                )
            except Exception:
                error_msg = "Unknown error"
            raise LabelboxError("Failed to upload, message: %s" % error_msg)

        csv_report = file_data["importUsersAsCsvToGroup"]["csvReport"]
        return self._parse_csv_report(csv_report)

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

    def _parse_csv_report(self, csv_report: str) -> List[dict]:
        lines = csv_report.strip().split("\n")
        headers = lines[0].split(",")
        report_list = []
        for line in lines[1:]:
            values = line.split(",")
            report_list.append(dict(zip(headers, values)))
        return report_list
