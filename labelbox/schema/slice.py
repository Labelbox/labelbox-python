from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.pagination import PaginatedCollection


class Slice(DbObject):
    """
    A Slice is a saved set of filters (saved query).
    This is an abstract class and should not be instantiated.

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

    def get_data_row_ids(self) -> PaginatedCollection:
        """
        Fetches all data row ids that match this Slice

        Returns:
            A PaginatedCollection of data row ids
        """
        query_str = """
            query getDataRowIdsBySavedQueryPyApi($id: ID!, $from: String, $first: Int!) {
                getDataRowIdsBySavedQuery(input: {
                    savedQueryId: $id,
                    after: $from
                    first: $first
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
        return PaginatedCollection(
            client=self.client,
            query=query_str,
            params={'id': self.uid},
            dereferencing=['getDataRowIdsBySavedQuery', 'nodes'],
            obj_class=lambda _, data_row_id: data_row_id,
            cursor_path=['getDataRowIdsBySavedQuery', 'pageInfo', 'endCursor'])
