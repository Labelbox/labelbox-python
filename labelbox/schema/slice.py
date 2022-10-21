from typing import List

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class Slice(DbObject):
    """
    A Slice is a saved set of filters (saved query)

    Attributes:
        name (datetime)
        description (datetime)
        created_at (datetime)
        updated_at (datetime)
        filter (json)
    """
    name = Field.String("name")
    description = Field.String("description")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    filter = Field.Json("filter")


class CatalogSlice(Slice):
    """
    Represents a Slice used for filtering data rows in Catalog.
    """

    def get_data_row_ids(self) -> List[str]:
        """
        Fetches all data row ids that match this Slice

        Returns:
            A list of data row ids
        """
        query_str = """
            query getDataRowIdsBySavedQueryPyApi($id: ID!, $after: String) {
                getDataRowIdsBySavedQuery(input: {
                    savedQueryId: $id,
                    after: $after
                }) {
                    totalCount
                    nodes
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        """
        data_row_ids: List[str] = []
        total_count = 0
        end_cursor = None
        has_next_page = True
        while has_next_page:
            res = self.client.execute(query_str, {
                'id': self.uid,
                'after': end_cursor
            })['getDataRowIdsBySavedQuery']
            data_row_ids = data_row_ids + res['nodes']
            total_count = res['totalCount']
            has_next_page = res['pageInfo']['hasNextPage']
            end_cursor = res['pageInfo']['endCursor']

        assert total_count == len(data_row_ids)
        return data_row_ids
